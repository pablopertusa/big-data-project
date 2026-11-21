# Este programa construye la tabla ZONA de la capa Silver a partir
# de los datos originales de la capa Bronze.
#
# Integra los nombres, polígonos, centroides y correspondencias
# territoriales del MITMA y del INE.
#
# Limpia y normaliza los identificadores territoriales, asigna las
# provincias, comunidades autónomas, municipios y GAU, y calcula
# la superficie de cada zona en kilómetros cuadrados.
#
# Finalmente, almacena la tabla en DuckDB y establece su clave
# primaria.

import duckdb
import pandas as pd
from pathlib import Path

# Rutas y conexión a DuckDB
proyecto = Path.home() / "Desktop" / "BigData_Project"
bronze = proyecto / "data" / "bronze"

con = duckdb.connect(str(proyecto / "lakehouse.duckdb"))

con.execute("INSTALL spatial")
con.execute("LOAD spatial")
con.execute("CREATE SCHEMA IF NOT EXISTS silver")

# Localizar los archivos
ruta_nombres = next(bronze.glob("MITMA_zonific*nombres.csv"))
ruta_correspondencia = bronze / "MITMA_INE_correspondencia.csv"
ruta_poligonos = next(bronze.rglob("zonificacion_distritos.shp"))
ruta_centroides = next(bronze.rglob("zonificacion_distritos_centroides.shp"))

# Leer los archivos de zonificación
nombres = pd.read_csv(ruta_nombres, sep="|", dtype=str)
correspondencia = pd.read_csv(ruta_correspondencia, sep="|", dtype=str)

# Obtener los códigos de provincia
correspondencia["provincia_id"] = correspondencia["municipio_ine"].str[:2]

# Corregir los códigos de los territorios especiales
especiales = correspondencia["distrito_mitma"].str.fullmatch(r"34\d{9}", na=False)

correspondencia.loc[especiales, "provincia_id"] = (
    correspondencia.loc[especiales, "distrito_mitma"].str[4:6]
)

# Obtener provincias y comunidades autónomas del INE
# Leer las provincias y comunidades autónomas de Bronze
ruta_provincias = bronze / "INE_provincias_comunidades.csv"

provincias = pd.read_csv(
    ruta_provincias,
    sep=";",
    encoding="utf-8-sig",
    dtype=str
)

provincias.columns = [
    "comunidad_autonoma_id",
    "comunidad_autonoma_nombre",
    "provincia_id",
    "provincia_nombre"
]

# Normalizar los códigos territoriales
provincias["provincia_id"] = (
    pd.to_numeric(provincias["provincia_id"], errors="coerce")
    .astype("Int64").astype("string").str.zfill(2)
)

provincias["comunidad_autonoma_id"] = (
    provincias["comunidad_autonoma_id"].astype(str).str.zfill(2)
)

# Obtener los nombres de los municipios
ruta_renta = bronze / "INE_renta.csv"

if not ruta_renta.exists():
    ruta_renta = bronze / "INE_income.csv"

municipios = pd.read_csv(
    ruta_renta, sep=None, engine="python",
    encoding="utf-8-sig", dtype=str
)

municipios.columns = municipios.columns.str.replace("\ufeff", "").str.strip()

municipios = municipios[["Municipios"]].dropna().drop_duplicates()

municipios["municipio_id"] = municipios["Municipios"].str.extract(r"^(\d{5})")

municipios["municipio_nombre"] = municipios["Municipios"].str.replace(
    r"^\d{5}\s+", "", regex=True
)

municipios = municipios.dropna(
    subset=["municipio_id"]
).drop_duplicates(subset=["municipio_id"])

# Registrar las tablas en DuckDB
con.register("nombres", nombres)
con.register("correspondencia", correspondencia)
con.register("provincias", provincias)
con.register("municipios", municipios)

# Importar las geometrías
con.execute("""
    CREATE TEMP TABLE poligonos AS
    SELECT * FROM ST_Read(?)
""", [str(ruta_poligonos)])

con.execute("""
    CREATE TEMP TABLE centroides AS
    SELECT * FROM ST_Read(?)
""", [str(ruta_centroides)])

# Eliminar temporalmente la tabla dependiente
con.execute("DROP TABLE IF EXISTS silver.relacion_festivos")


# Construir la tabla Silver ZONA
con.execute("""
    CREATE OR REPLACE TABLE silver.zona AS

    WITH territorio AS (
        SELECT DISTINCT distrito_mitma, provincia_id,
                        municipio_mitma, gau_mitma
        FROM correspondencia
    )

    SELECT
        n.ID AS ID,
        n.name AS Nombre,
        p.geom AS Poligono,
        c.geom AS Centroide,
        t.provincia_id AS Provincia_id,
        pr.provincia_nombre AS Provincia_nombre,
        pr.comunidad_autonoma_id AS Comunidad_autonoma_id,
        pr.comunidad_autonoma_nombre AS Comunidad_autonoma_nombre,
        t.municipio_mitma AS Municipio_id,
        COALESCE(nm.name, m.municipio_nombre) AS Municipio_nombre,
        t.gau_mitma AS GAU_id,

        COALESCE(
            ng.name,
            mg.municipio_nombre,
            CASE WHEN t.gau_mitma LIKE 'GAU %'
                 THEN t.gau_mitma END
        ) AS GAU_nombre,

        ST_Area(p.geom) / 1000000.0 AS Superficie

    FROM nombres n
    LEFT JOIN poligonos p ON n.ID = p.ID
    LEFT JOIN centroides c ON n.ID = c.ID
    LEFT JOIN territorio t ON n.ID = t.distrito_mitma
    LEFT JOIN provincias pr ON t.provincia_id = pr.provincia_id
    LEFT JOIN municipios m ON t.municipio_mitma = m.municipio_id
    LEFT JOIN nombres nm ON t.municipio_mitma = nm.ID
    LEFT JOIN nombres ng ON t.gau_mitma = ng.ID
    LEFT JOIN municipios mg ON t.gau_mitma = mg.municipio_id
""")

# Establecer la clave primaria
con.execute("ALTER TABLE silver.zona ADD PRIMARY KEY (ID)")

# Mostrar los resultados
print(con.execute("""
    SELECT ID, Nombre, Provincia_nombre,
           Municipio_nombre, GAU_nombre, Superficie
    FROM silver.zona
    LIMIT 10
""").df())

# Exportar la tabla a CSV
ruta_silver = proyecto / "data" / "silver"
ruta_silver.mkdir(exist_ok=True)

con.execute(f"""
    COPY silver.zona
    TO '{ruta_silver / "ZONA.csv"}'
    (FORMAT CSV, HEADER, DELIMITER ';')
""")

con.close()