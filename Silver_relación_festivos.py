# Este programa relaciona los festivos de 2023 con las
# zonas donde se celebran, utilizando el calendario de
# Bronze y las tablas FESTIVOS y ZONA de Silver.

import pandas as pd
import duckdb
from pathlib import Path
from datetime import date

# Rutas del proyecto
proyecto = Path.home() / "Desktop" / "BigData_Project"
bronze = proyecto / "data" / "bronze"
silver = proyecto / "data" / "silver"

silver.mkdir(exist_ok=True)

# Conexión a DuckDB
con = duckdb.connect(str(proyecto / "lakehouse.duckdb"))
con.execute("LOAD spatial")

# Leer el calendario original
calendario = pd.read_csv(
    bronze / "BOE_calendario_festivos.csv",
    sep=";",
    encoding="utf-8-sig"
)

meses = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3,
    "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
    "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9,
    "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

# Códigos INE de las comunidades autónomas
comunidades = {
    "Andalucía": "01",
    "Aragón": "02",
    "Asturias": "03",
    "Illes Balears": "04",
    "Canarias (1)": "05",
    "Cantabria": "06",
    "Castilla y León": "07",
    "Castilla-La Mancha": "08",
    "Cataluña (2)": "09",
    "Comunitat Valenciana": "10",
    "Extremadura": "11",
    "Galicia": "12",
    "Com. Madrid": "13",
    "Región Murcia": "14",
    "C. Foral Navarra": "15",
    "País Vasco": "16",
    "La Rioja": "17",
    "Ciudad de Ceuta (3)": "18",
    "Ciudad de Melilla": "19"
}

relaciones = []

# Identificar los festivos de cada comunidad
for _, fila in calendario.iterrows():

    texto = str(fila["Fecha de las fiestas"]).strip()

    if texto in meses:
        mes = meses[texto]
        continue

    if pd.isna(fila["Fecha de las fiestas"]):
        continue

    dia, nombre = texto.split(" ", 1)
    fecha = date(2023, mes, int(dia))
    nombre = nombre.strip().rstrip(".")

    for comunidad, codigo in comunidades.items():

        if str(fila[comunidad]).strip() in ("*", "**", "***"):
            relaciones.append((fecha, nombre, codigo))

# Registrar las correspondencias en DuckDB
df = pd.DataFrame(
    relaciones,
    columns=["fecha", "nombre_festivo", "comunidad_id"]
)

con.register("relaciones", df)

# Comprobar que todos los festivos tienen correspondencia
faltantes = con.execute("""
    SELECT DISTINCT r.fecha, r.nombre_festivo
    FROM relaciones r
    LEFT JOIN silver.festivos f
        ON r.fecha = f.fecha
        AND r.nombre_festivo = f.nombre_festivo
    WHERE f.id_festivo IS NULL
""").df()

if not faltantes.empty:
    print(faltantes)
    raise ValueError("Hay festivos sin correspondencia")

# Crear la tabla Silver
con.execute("""
    CREATE OR REPLACE TABLE silver.relacion_festivos (
        id_festivo INTEGER REFERENCES silver.festivos(id_festivo),
        id_zona VARCHAR REFERENCES silver.zona(ID),
        PRIMARY KEY (id_festivo, id_zona)
    )
""")

# Relacionar festivos y zonas
con.execute("""
    INSERT INTO silver.relacion_festivos

    SELECT DISTINCT f.id_festivo, z.ID
    FROM relaciones r

    JOIN silver.festivos f
        ON r.fecha = f.fecha
        AND r.nombre_festivo = f.nombre_festivo

    JOIN silver.zona z
        ON r.comunidad_id = z.Comunidad_autonoma_id
""")

# Mostrar los resultados
print(con.execute("""
    SELECT *
    FROM silver.relacion_festivos
    ORDER BY id_festivo, id_zona
    LIMIT 10
""").df())

print(con.execute("""
    SELECT COUNT(*) AS total_relaciones
    FROM silver.relacion_festivos
""").df())

# Exportar a CSV
con.execute("""
    COPY silver.relacion_festivos
    TO ? (HEADER, DELIMITER ';')
""", [str(silver / "RELACION_FESTIVOS.csv")])

con.close()