"""Descarga originales MITMA, sin transformar ni extraer los datos."""

import argparse
from collections import Counter
from datetime import date, timedelta
from http.client import HTTPException
from pathlib import Path
import shutil
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET


BASE_URL = "https://mitma-movilidad-v2.s3.eu-west-1.amazonaws.com"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "data" / "mitma"
LEVELS = ("distritos", "municipios", "GAU")
INDICATORS = {"viajes": "Viajes", "pernoctaciones": "Pernoctaciones", "personas": "Personas_dia"}
DOCUMENTS = (
    "LEEME_Especificaciones_indicadores_OpenDataMovilidad.xlsx",
    "LICENCIA de datos abiertos del MITMA 20201203.pdf",
)
NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("diario", "mensual"), default="diario")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD (diario) o YYYY-MM (mensual)")
    parser.add_argument("--end", required=True, help="Extremo final incluido; mismo formato que --start")
    parser.add_argument("--levels", nargs="+", choices=LEVELS, default=list(LEVELS))
    parser.add_argument("--auxiliares", action="store_true", help="Incluir zonificación y documentación")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true", help="Consultar archivos y tamaños sin descargar")
    parser.add_argument("--overwrite", action="store_true", help="Sustituir archivos finales existentes")
    args = parser.parse_args()
    try:
        suffix = "-01" if args.mode == "mensual" else ""
        start = date.fromisoformat(args.start + suffix)
        end = date.fromisoformat(args.end + suffix)
        if start.isoformat() != args.start + suffix or end.isoformat() != args.end + suffix:
            raise ValueError("Formato de fecha incorrecto")
        args.start, args.end = start, end
    except ValueError:
        parser.error("Fechas inválidas: usa YYYY-MM-DD en modo diario o YYYY-MM en mensual.")
    if args.start > args.end:
        parser.error("--start no puede ser posterior a --end.")
    args.levels = list(dict.fromkeys(args.levels))
    return args


def open_url(url):
    """Tres intentos para fallos de red o respuestas transitorias del servidor."""
    for attempt in range(3):
        try:
            return urlopen(url, timeout=60)
        except HTTPError as error:
            if error.code not in (408, 429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (URLError, TimeoutError, HTTPException):
            if attempt == 2:
                raise
        time.sleep(attempt + 1)


def list_files(prefix):
    """Lista objetos públicos S3, incluida la paginación; no necesita boto3."""
    files = {}
    params = {"list-type": "2", "prefix": prefix}
    while True:
        with open_url(BASE_URL + "/?" + urlencode(params)) as response:
            root = ET.parse(response).getroot()
        for item in root.findall("s3:Contents", NS):
            key = item.findtext("s3:Key", namespaces=NS)
            if not key.endswith("/"):
                files[key] = int(item.findtext("s3:Size", namespaces=NS))
        token = root.findtext("s3:NextContinuationToken", namespaces=NS)
        if not token:
            return files
        params["continuation-token"] = token


def daily_files(args):
    """Genera pares (clave remota, destino relativo), también para los TAR mensuales."""
    current = args.start
    while current <= args.end:
        stamp = current.strftime("%Y%m%d" if args.mode == "diario" else "%Y%m")
        remote_folder = (
            f"ficheros-diarios/{current:%Y-%m}" if args.mode == "diario" else "meses-completos"
        )
        local_folder = "diarios" if args.mode == "diario" else "meses-completos"
        extension = "csv.gz" if args.mode == "diario" else "tar"
        for level in args.levels:
            for indicator, name in INDICATORS.items():
                folder = f"por-{level}/{indicator}"
                filename = f"{stamp}_{name}_{level}.{extension}"
                yield (
                    f"estudios_basicos/{folder}/{remote_folder}/{filename}",
                    Path(folder) / local_folder / filename,
                )
        if args.mode == "diario":
            current += timedelta(days=1)
        else:
            current = date(current.year + current.month // 12, current.month % 12 + 1, 1)

    # Calidad solo se publica por días, también cuando se descargan meses completos.
    current = args.start
    end = args.end
    if args.mode == "mensual":
        end = date(end.year + end.month // 12, end.month % 12 + 1, 1) - timedelta(days=1)
    while current <= end:
        filename = f"{current:%Y%m%d}_distritos_descartados.csv"
        yield (
            f"estudios_basicos/calidad/ficheros-diarios/{current:%Y-%m}/{filename}",
            Path("calidad/diarios") / filename,
        )
        current += timedelta(days=1)


def auxiliary_files(levels):
    files = {}
    for level in levels:
        files.update(list_files(f"zonificacion/zonificacion_{level}/"))
    required = ["zonificacion/poblacion.csv", "zonificacion/relacion_ine_zonificacionMitma.csv"]
    required.extend(DOCUMENTS)
    for key in required:
        files.update({k: size for k, size in list_files(key).items() if k == key})
    return sorted(set(files) | set(required)), files


def download_file(key, destination, size):
    """Solo publica el archivo final tras descargarlo completo; reintenta desde cero."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".part")
    try:
        for attempt in range(3):
            try:
                with open_url(BASE_URL + "/" + quote(key, safe="/")) as response:
                    with temporary.open("wb") as output:
                        shutil.copyfileobj(response, output, length=1024 * 1024)
                if temporary.stat().st_size != size:
                    raise OSError("El tamaño descargado no coincide con el catálogo.")
                temporary.replace(destination)
                return
            except HTTPError:
                raise  # open_url ya ha reintentado los errores HTTP transitorios.
            except (URLError, OSError, EOFError, HTTPException) as error:
                if attempt == 2:
                    raise
                print(f"  Reintentando transferencia: {error}", flush=True)
                time.sleep(attempt + 1)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    args = parse_args()
    requested = list(daily_files(args))
    print("Consultando catálogo público MITMA…", flush=True)
    catalog = {}
    for prefix in sorted({key.rsplit("/", 1)[0] + "/" for key, _ in requested}):
        catalog.update(list_files(prefix))
    if args.auxiliares:
        auxiliary_keys, auxiliaries = auxiliary_files(args.levels)
        catalog.update(auxiliaries)
        for key in auxiliary_keys:
            requested.append((key, Path(key.replace("zonificacion/", "zonificación/", 1))))

    total = sum(catalog.get(key, 0) for key, _ in requested)
    pending = sum(
        catalog.get(key, 0) for key, relative in requested
        if args.overwrite or not (args.output / relative).exists()
    )
    print(f"Destino: {args.output.resolve()}")
    print(f"Solicitados: {len(requested)} archivos; {total / 1e9:.3f} GB publicados.")
    print(f"Pendientes de descarga: {pending / 1e9:.3f} GB (tamaños decimales).", flush=True)
    counts = Counter()
    for key, relative in requested:
        destination = args.output / relative
        if key not in catalog:
            status = "ausente"
        elif destination.exists() and not args.overwrite:
            status = "omitido"
        elif args.dry_run:
            status = "previsto"
        else:
            print(f"Descargando {relative} ({catalog[key] / 1e6:.2f} MB)…", flush=True)
            try:
                download_file(key, destination, catalog[key])
                status = "descargado"
            except (OSError, URLError, EOFError, HTTPException) as error:
                print(f"  Error: {error}", file=sys.stderr)
                status = "fallido"
        counts[status] += 1
        print(f"[{status}] {relative}", flush=True)
    print("Resumen: " + ", ".join(f"{status}={number}" for status, number in sorted(counts.items())))
    return 1 if counts["ausente"] or counts["fallido"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, URLError, HTTPException, ET.ParseError) as error:
        print(f"Error consultando MITMA: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDescarga interrumpida. Puedes repetir el mismo comando.", file=sys.stderr)
        sys.exit(130)
