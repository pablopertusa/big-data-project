from pathlib import Path

import cdsapi

data_dir = Path(__file__).resolve().parents[1] / "data" / "copernicus"
data_dir.mkdir(parents=True, exist_ok=True)

dataset = "reanalysis-era5-land-timeseries"
request = {
    "variable": [
        "2m_temperature",
        "total_precipitation",
        "snowfall",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind"
    ],
    "date": ["2022-01-01/2024-12-31"],
    "data_format": "netcdf",
    # Norte, oeste, sur, este: península, Baleares, Canarias, Ceuta y Melilla.
    "area": [44.0, -18.5, 27.5, 4.5]
}

client = cdsapi.Client()
destination = data_dir / "era5_land_2022_2024.nc"
client.retrieve(dataset, request).download(str(destination))
print(f"Descargado: {destination}")
