from pathlib import Path
from urllib.request import urlretrieve

data_dir = Path(__file__).resolve().parents[1] / "data"
data_dir.mkdir(parents=True, exist_ok=True)

base_url = (
    "https://www.dgt.es/export/sites/web-DGT/.galleries/downloads/"
    "dgt-en-cifras/informacion_municipal/Datos-municipales-general"
)

for year in (2022, 2023, 2024):
    filename = f"DatosMunicipalesGeneral_{year}.xlsx"
    destination = data_dir / filename
    urlretrieve(f"{base_url}/{filename}", destination)
    print(f"Descargado: {destination}")
