# Este programa extrae la tabla oficial del INE que
# relaciona las provincias con las comunidades autónomas
# y sus respectivos códigos.
#
# Los datos se almacenan en formato CSV dentro de la capa
# Bronze para su posterior utilización en la capa Silver.

import pandas as pd
from pathlib import Path

# Ruta de la carpeta Bronze
proyecto = Path.home() / "Desktop" / "BigData_Project"
bronze = proyecto / "data" / "bronze"

# Fuente oficial del INE
url = "https://www.ine.es/daco/daco42/codmun/cod_ccaa_provincia.htm"

# Extraer la tabla
df = pd.read_html(
    url,
    match="CODAUTO",
    encoding="ISO-8859-1"
)[0]

# Guardar los datos en Bronze
df.to_csv(
    bronze / "INE_provincias_comunidades.csv",
    sep=";",
    encoding="utf-8-sig",
    index=False
)

# Mostrar los datos obtenidos
print(df)
print("Archivo guardado correctamente en Bronze")