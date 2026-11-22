# Big Data Project

en progreso

## Carga local de Bronce y Plata

Instala las dependencias con `uv sync --locked` y ejecuta los notebooks en orden:

1. [`notebooks/01_bronze.ipynb`](notebooks/01_bronze.ipynb) carga las fuentes en el esquema `bronze`.
2. [`notebooks/silver.ipynb`](notebooks/silver.ipynb) construye `silver.zona`, con una fila por distrito MITMA, y `silver.festivos` y `silver.relacion_festivos` a partir del cuadro nacional y autonómico del BOE de 2023.

Ambos usan `data/processed/database.duckdb`. Los notebooks no descargan datos ni requieren `data/bronze/`. Las fuentes se preparan antes de ejecutarlos:

| Carpeta | Entradas |
|---|---|
| `data/mitma/` | Viajes y pernoctaciones diarios por distrito, y archivos de zonificación. |
| `data/ine/` | Población, estudios y relación con la actividad por país de nacimiento; catálogos territorial y municipal; `renta.csv` y `rama_actividad.csv`. |
| `data/dgt/` | `DatosMunicipalesGeneral_2022.xlsx`, `DatosMunicipalesGeneral_2023.xlsx` y `DatosMunicipalesGeneral_2024.xlsx`. El CSV alternativo de 2023 no se necesita. |
| `data/boe/` | `calendario_festivos_2023.csv`, generado con `uv run --locked python scripts/download_boe_festivos.py`. |
| `data/copernicus/` | Series horarias ERA5-Land (2022–2024), una descarga por centroide de distrito MITMA. |

Los archivos ignorados por Git deben estar disponibles localmente. Las fuentes nuevas de INE proceden del lote compartido y no están incluidas en el repositorio.

### Copernicus

Configura `~/.cdsapirc` y [acepta la licencia del dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=download#manage-licences) con la misma cuenta. Desde la raíz del proyecto:

```bash
uv run --locked python scripts/download_copernicus.py --dry-run
uv run --locked python scripts/download_copernicus.py --district 01001
uv run --locked python scripts/download_copernicus.py
```

El primer comando no usa la red, el segundo prueba un distrito y el tercero descarga todos, incluidos los distritos extranjeros del catálogo MITMA. Repite el mismo comando para reanudar. La sección Copernicus del notebook Bronze carga lo disponible en `bronze.copernicus_horario` (una fila por distrito y hora UTC) e informa de los periodos pendientes y valores ausentes.

![](https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExeTB0eW13MTlrbzRieGFuNGxrOG9xZDBlN2Y5d2dzaWY4b3U5MHdqaSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/y6Sl42U3xEFkk/giphy.gif)
