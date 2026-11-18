"""Descarga datos climatológicos diarios de todas las estaciones de AEMET."""

import argparse
from datetime import date, timedelta
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "aemet"
BASE_URL = "https://opendata.aemet.es/opendata/api"


def load_api_key():
    """Lee la clave del entorno o del archivo .env en la raíz del proyecto."""
    api_key = os.environ.get("AEMET_API_KEY", "").strip()
    if not api_key and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
            name, separator, value = line.strip().partition("=")
            if separator and name.strip() == "AEMET_API_KEY":
                api_key = value.strip().strip("\"'")
                break
    if not api_key:
        raise ValueError("Añade tu clave a AEMET_API_KEY en el archivo .env.")
    return api_key


def fetch_json(url, api_key=None):
    # La clave solo se envía a la API, no al enlace de descarga que devuelve.
    headers = {"api_key": api_key} if api_key else {}
    with urlopen(Request(url, headers=headers), timeout=120) as response:
        content = response.read()
        encoding = response.headers.get_content_charset()
    if encoding:
        return json.loads(content.decode(encoding))
    try:
        return json.loads(content.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(content.decode("iso-8859-15"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, type=date.fromisoformat, help="Fecha inicial: YYYY-MM-DD")
    parser.add_argument("--end", required=True, type=date.fromisoformat, help="Fecha final incluida: YYYY-MM-DD")
    args = parser.parse_args()
    if args.start > args.end:
        parser.error("--start no puede ser posterior a --end.")

    api_key = load_api_key()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    start = args.start
    while start <= args.end:
        # Tramos de hasta 15 días para limitar el tamaño de cada petición.
        end = min(start + timedelta(days=14), args.end)
        destination = DATA_DIR / f"aemet_diarios_{start}_{end}.json"
        if destination.exists():
            print(f"Ya existe: {destination.name}", flush=True)
        else:
            url = (
                f"{BASE_URL}/valores/climatologicos/diarios/datos"
                f"/fechaini/{start}T00:00:00UTC"
                f"/fechafin/{end}T23:59:59UTC/todasestaciones"
            )
            print(f"Consultando AEMET: {start} a {end}", flush=True)
            try:
                response = fetch_json(url, api_key)
            except HTTPError as error:
                if error.code != 404:
                    raise
                response = {"estado": 404}

            status = int(response.get("estado", 0))
            if status == 404:
                print("Sin datos para este tramo.", flush=True)
            elif status != 200:
                raise ValueError(
                    f"AEMET ({status}): {response.get('descripcion', 'Respuesta inesperada')}"
                )
            else:
                records = fetch_json(response["datos"])
                # Se conservan los campos y valores originales, sin transformar.
                content = json.dumps(records, ensure_ascii=False, indent=2)
                temporary = destination.with_suffix(".json.part")
                temporary.write_text(content + "\n", encoding="utf-8")
                temporary.replace(destination)
                print(f"Descargado: {destination.name} ({len(records)} registros)", flush=True)
            # Evita encadenar peticiones demasiado deprisa.
            time.sleep(2)
        start = end + timedelta(days=1)


if __name__ == "__main__":
    try:
        main()
    except HTTPError as error:
        raise SystemExit(f"Error HTTP {error.code}. Revisa la clave y los límites de AEMET.") from None
    except (URLError, TimeoutError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from None
