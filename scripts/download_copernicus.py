"""Download hourly ERA5-Land for every MITMA district centroid (2022–2024)."""

import argparse
from contextlib import ExitStack
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile, is_zipfile

import cdsapi
import geopandas as gpd
import pandas as pd
from requests import RequestException


ROOT = Path(__file__).resolve().parents[1]
CENTROIDS = ROOT / (
    "data/mitma/zonificación/zonificacion_distritos/zonificacion_distritos_centroides.shp"
)
OUTPUT = ROOT / "data/copernicus"
DATASET = "reanalysis-era5-land-timeseries"
LICENCE_URL = f"https://cds.climate.copernicus.eu/datasets/{DATASET}?tab=download#manage-licences"
VARIABLES = {
    "2m_temperature": ("t2m", "2t"),
    "total_precipitation": ("tp",),
    "snowfall": ("sf",),
    "10m_u_component_of_wind": ("u10", "10u"),
    "10m_v_component_of_wind": ("v10", "10v"),
}
YEARS = tuple((f"{year}-01-01", f"{year}-12-31") for year in range(2022, 2025))
FULL_PERIOD = (YEARS[0][0], YEARS[-1][1])
ASSET_ERRORS = (ValueError, OSError, BadZipFile)


def read_centroids(path=CENTROIDS):
    districts = gpd.read_file(path)
    ids = districts["ID"].astype("string")
    if ids.isna().any() or not ids.str.fullmatch(r"[A-Za-z0-9_-]+").all() or not ids.is_unique:
        raise ValueError("MITMA district IDs must be nonempty, unique and safe as directory names.")
    if districts.crs is None or not districts.geom_type.eq("Point").all():
        raise ValueError("MITMA centroid file must contain points with a defined CRS.")
    points = districts.to_crs("EPSG:4326")
    if not (points.geometry.x.between(-180, 180) & points.geometry.y.between(-90, 90)).all():
        raise ValueError("Invalid MITMA centroid coordinates.")
    return dict(zip(ids, zip(points.geometry.y, points.geometry.x), strict=True))


def asset_path(output, district, period):
    start, end = period
    # Keep the original CDS response, which may be a CSV or a ZIP of group CSVs.
    return output / district / f"{start}_{end}.cds"


def available_assets(output, district):
    full = asset_path(output, district, FULL_PERIOD)
    if full.is_file():
        return [(FULL_PERIOD, full)]
    return [(period, path) for period in YEARS if (path := asset_path(output, district, period)).is_file()]


def expected_hours(period):
    start, end = period
    return pd.date_range(start, pd.Timestamp(end) + pd.Timedelta(hours=23), freq="h", tz="UTC")


def read_hourly_asset(path, period):
    """Validate a CDS point response; return UTC-indexed values and count missing hours."""
    expected = expected_hours(period)
    columns = {}
    observed = expected
    with ExitStack() as stack:
        if is_zipfile(path):
            archive = stack.enter_context(ZipFile(path))
            sources = (archive.open(member) for member in archive.namelist() if member.lower().endswith(".csv"))
        else:
            sources = (path.open("rb") for _ in range(1))
        for source in sources:
            with source:
                frame = pd.read_csv(source)
            time_column = next((name for name in ("time", "valid_time") if name in frame), None)
            if time_column is None or frame.empty:
                raise ValueError(f"{path.name}: no hourly timestamps")
            times = pd.DatetimeIndex(pd.to_datetime(frame[time_column], format="ISO8601", utc=True))
            if not times.is_unique or not times.isin(expected).all():
                raise ValueError(f"{path.name}: duplicate or out-of-period/non-hourly timestamps")
            observed = observed.intersection(times)
            for variable, aliases in VARIABLES.items():
                names = [name for name in (variable, *aliases) if name in frame]
                if not names:
                    continue
                if variable in columns or len(names) != 1:
                    raise ValueError(f"{path.name}: duplicate variable {variable}")
                values = pd.to_numeric(frame[names[0]], errors="raise").astype("float64")
                columns[variable] = pd.Series(values.array, index=times).replace(
                    [float("inf"), -float("inf")], float("nan")
                )
    if missing := VARIABLES.keys() - columns.keys():
        raise ValueError(f"{path.name}: missing variables: {', '.join(sorted(missing))}")
    # Keep absent hours as NULL, not zero, and distinguish them from missing values.
    return pd.DataFrame(columns, index=expected)[list(VARIABLES)], len(expected.difference(observed))


def fetch_period(client, district, point, period, output, *, overwrite):
    target = asset_path(output, district, period)
    if target.is_file() and not overwrite:
        try:
            read_hourly_asset(target, period)
        except ASSET_ERRORS as error:
            print(f"[{district}] Redownloading invalid file: {error}", file=sys.stderr)
        else:
            print(f"[{district}] Already downloaded: {target.name}", flush=True)
            return
    latitude, longitude = point
    request = {
        "variable": list(VARIABLES),
        "location": {"latitude": latitude, "longitude": longitude},
        "date": ["/".join(period)],
        "data_format": "csv",
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".part")
    print(f"[{district}] Requesting {' / '.join(period)}", flush=True)
    try:
        client.retrieve(DATASET, request).download(str(partial))
        _, missing_hours = read_hourly_asset(partial, period)
        partial.replace(target)
        print(f"[{district}] Saved {target.name} (missing hours: {missing_hours})", flush=True)
    finally:
        partial.unlink(missing_ok=True)


def download_district(client, district, point, output, *, overwrite):
    assets = available_assets(output, district)
    full = asset_path(output, district, FULL_PERIOD)
    if not assets or assets[0][0] == FULL_PERIOD:
        try:
            fetch_period(client, district, point, FULL_PERIOD, output, overwrite=overwrite)
            return
        except RequestException as error:
            if "cost limits exceeded" not in str(error).lower():
                raise
            print(f"[{district}] Request too large; splitting by year.", flush=True)
    for period in YEARS:
        fetch_period(client, district, point, period, output, overwrite=overwrite)
    # A full file that was invalid or explicitly refreshed must not mask the annual files.
    full.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--district", action="append", help="Only this MITMA ID; repeat for a pilot.")
    parser.add_argument("--dry-run", action="store_true", help="List the scope without contacting the CDS.")
    parser.add_argument("--overwrite", action="store_true", help="Refresh previously downloaded assets.")
    args = parser.parse_args()
    districts = read_centroids()
    if args.district:
        if unknown := set(args.district) - districts.keys():
            parser.error(f"Unknown MITMA district IDs: {', '.join(sorted(unknown))}")
        districts = {district: districts[district] for district in dict.fromkeys(args.district)}
    print(f"MITMA districts selected: {len(districts):,}")
    if args.dry_run:
        present = sum(bool(available_assets(OUTPUT, district)) for district in districts)
        print(f"Districts with local assets (not validated): {present:,}. Destination: {OUTPUT}")
        return 0

    client = cdsapi.Client()
    failed = []
    for district, point in sorted(districts.items()):
        try:
            download_district(client, district, point, OUTPUT, overwrite=args.overwrite)
        except (RequestException, *ASSET_ERRORS) as error:
            message = str(error).lower()
            if "licences not accepted" in message:
                print(f"Accept the Copernicus dataset licence and run again: {LICENCE_URL}", file=sys.stderr)
                return 1
            if "401 client error" in message or (
                "403 client error" in message and "cost limits exceeded" not in message
            ):
                print(f"CDS access denied; stopping: {error}", file=sys.stderr)
                return 1
            print(f"[{district}] Failed: {error}", file=sys.stderr, flush=True)
            failed.append(district)
    print(f"Districts completed: {len(districts) - len(failed):,}; failed: {len(failed):,}")
    if failed:
        print(f"Failed district IDs: {', '.join(failed)}", file=sys.stderr)
    return int(bool(failed))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit("\nDownload interrupted. Run the same command to resume.")
