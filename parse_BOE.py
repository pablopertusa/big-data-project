# Este programa realiza la extracción del calendario oficial de
# festivos de 2023 publicado en el Boletín Oficial del Estado (BOE).
#
# Mediante pandas, obtiene la primera tabla HTML de la página web
# y la exporta a un fichero CSV llamado calendario_festivos.csv.
#
# Este proceso forma parte de la ingesta de datos de la capa Bronze,
# conservando la estructura original del calendario para su posterior
# limpieza y transformación en la capa Silver.

import pandas as pd

url = "https://www.boe.es/buscar/doc.php?id=BOE-A-2022-16755"

df = pd.read_html(url)[0]

df.to_csv(
    "BOE_calendario_festivos.csv",
    index=False,
    sep=";",
    encoding="utf-8-sig",
    header=False
)