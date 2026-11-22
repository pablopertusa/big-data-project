# Bronze: de los ficheros a DuckDB

Ejecutar `notebooks/01_bronze.ipynb` de arriba abajo con las descargas locales en `data/`. Escribe en el esquema `bronze` de `data/processed/database.duckdb`. Cada fila conserva `_archivo` (ruta relativa al proyecto) y `_timestamp` (instante de carga UTC). Los identificadores y valores de origen se leen como texto para conservar ceros iniciales, formatos locales y categorías. La normalización analítica se hace en [Silver](silver.md).

| Bloque del notebook | Entrada y transformación |
|---|---|
| MITMA · Viajes por distrito | Lee los `*_Viajes_distritos.csv.gz` diarios, separados por `\|`, en `mitma_viajes`. Las fechas opcionales filtran por nombre de fichero, con ambos extremos incluidos. Se sustituyen las filas del archivo recargado; se conservan periodo, dimensiones y medidas originales. |
| MITMA · Pernoctaciones por distrito | Misma mecánica con selección de fechas independiente. `mitma_pernoctaciones` conserva fecha, residencia, zona de pernoctación y personas. |
| MITMA · Zonificación | Lee los shapefiles de polígonos y centroides de distrito como WKT con su CRS. `mitma_relacion_ine` conserva la correspondencia original por sección. Los tres catálogos de nombres se reúnen en `mitma_nombres_zonas` con su `tipo_zona`. Estas tablas se reconstruyen al cargar. |
| INE · Población, estudios y situación laboral | Reconstruye `ine_poblacion` desde CSV tabulado, e `ine_nivel_estudios` e `ine_relacion_actividad` desde tabulados. Se conservan tanto las filas de sección como los agregados publicados. Las muestras pueden acabar en una fila incompleta. |
| INE · Catálogos territoriales | `ine_municipios` lee las columnas A:E del diccionario Excel desde la cabecera de la fila 2; `ine_provincias_ccaa` lee la correspondencia de provincias y comunidades del CSV. |
| INE · Renta y rama de actividad | Reconstruye `ine_renta` desde el tabulado UTF-8 e `ine_rama_actividad` desde el tabulado UTF-8. Conserva indicadores, categorías, periodos y totales tal como aparecen. |
| DGT · Datos municipales | Reúne los Excel municipales 2022–2024 en `dgt_datos_municipales`, sustituyendo las filas de cada archivo recargado. El año permanece en `_archivo`. |
| BOE · Calendario laboral | `boe_calendario_festivos_2023` conserva las filas de mes, las descripciones de fiesta y las columnas originales con las marcas por comunidad del CSV de 2023. |
| Copernicus · Series horarias | Lee los activos CDS locales por distrito mediante el lector de `scripts/download_copernicus.py`. Se prefiere el archivo del periodo completo; en su defecto se leen los anuales disponibles. Alinea las cinco variables por hora UTC, conserva ausencias como nulos y reemplaza la ventana temporal recargada en `copernicus_horario`. |
