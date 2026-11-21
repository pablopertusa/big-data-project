# Este programa construye la tabla FESTIVOS de la capa Silver
# a partir del calendario de festivos de 2023 de la capa Bronze.
# Transforma las fechas, limpia los nombres de los festivos
# y asigna un identificador único a cada registro.
# Finalmente, almacena la tabla en DuckDB y valida sus datos.

import csv
import duckdb
from datetime import date
from pathlib import Path

# Rutas del proyecto
proyecto = Path.home() / "Desktop" / "BigData_Project"
bronze = proyecto / "data" / "bronze"

ruta = bronze / "BOE_calendario_festivos.csv"

# Conexión a DuckDB
con = duckdb.connect(str(proyecto / "lakehouse.duckdb"))
con.execute("CREATE SCHEMA IF NOT EXISTS silver")

# Correspondencia entre meses y números
meses = {
    "ENERO": 1,
    "FEBRERO": 2,
    "MARZO": 3,
    "ABRIL": 4,
    "MAYO": 5,
    "JUNIO": 6,
    "JULIO": 7,
    "AGOSTO": 8,
    "SEPTIEMBRE": 9,
    "OCTUBRE": 10,
    "NOVIEMBRE": 11,
    "DICIEMBRE": 12
}

festivos = []

# Leer y transformar el calendario original
with open(ruta, encoding="utf-8-sig") as archivo:

    lector = csv.DictReader(archivo, delimiter=";")

    for fila in lector:

        texto = fila["Fecha de las fiestas"].strip()

        if not texto:
            continue

        # Identificar el mes
        if texto in meses:
            mes = meses[texto]
            continue

        # Separar el día y el nombre del festivo
        dia, nombre = texto.split(" ", 1)
        nombre = nombre.strip().rstrip(".")

        # Construir la fecha completa
        fecha = date(2023, mes, int(dia))

        # Generar un identificador consecutivo
        id_festivo = len(festivos) + 1

        festivos.append((id_festivo, fecha, nombre))

# Crear la tabla FESTIVOS
con.execute("""
    CREATE OR REPLACE TABLE silver.festivos (
        id_festivo INTEGER PRIMARY KEY,
        fecha DATE NOT NULL,
        nombre_festivo VARCHAR NOT NULL
    )
""")

# Insertar los registros
con.executemany("""
    INSERT INTO silver.festivos VALUES (?, ?, ?)
""", festivos)

# Mostrar los resultados
print(con.execute("""
    SELECT *
    FROM silver.festivos
    ORDER BY fecha, id_festivo
""").df())

# Exportar la tabla FESTIVOS a CSV
ruta_silver = proyecto / "data" / "silver"
ruta_silver.mkdir(exist_ok=True)

con.execute(f"""
    COPY silver.festivos
    TO '{ruta_silver / "FESTIVOS.csv"}'
    (FORMAT CSV, HEADER, DELIMITER ';')
""")

con.close()

con.close()