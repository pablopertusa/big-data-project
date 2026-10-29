# Datos de movilidad MITMA

## Descarga

Desde la raíz del repositorio, con Python 3.12 y el entorno del proyecto:

```bash
uv sync --locked

# Una semana: viajes, pernoctaciones y personas en los tres niveles, más auxiliares.
uv run python scripts/download_mitma.py \
  --start 2023-01-01 --end 2023-01-07 --auxiliares

# Paquetes de meses completos, solo municipios.
uv run python scripts/download_mitma.py \
  --mode mensual --start 2023-01 --end 2023-12 --levels municipios

# Consultar disponibilidad y volumen sin descargar ni crear archivos.
uv run python scripts/download_mitma.py \
  --mode mensual --start 2023-01 --end 2023-12 --dry-run
```

- `--mode diario` (predeterminado): fechas `YYYY-MM-DD`, descarga `.csv.gz`.
- `--mode mensual`: fechas `YYYY-MM`, descarga `.tar` de meses completos.
  Son paquetes de archivos diarios, **no agregados mensuales**. No se extraen automáticamente.
- Ambos extremos del intervalo están incluidos. Las fechas son obligatorias.
- `--levels` admite uno o varios valores: `distritos municipios GAU`; por defecto, los tres.
- Los distritos descartados (calidad) se descargan por día en ambos modos, una vez por fecha.
- `--auxiliares` incluye nombres, población, todos los componentes publicados de las zonas
  y centroides de los niveles seleccionados, correspondencia INE–MITMA, población auxiliar,
  diccionario y licencia. No incluye la zonificación especial de matrices de tiempos.
- `--output RUTA` cambia el destino; por defecto es `data/mitma/` dentro del repositorio,
  independientemente del directorio desde el que se ejecute el script.
- Los archivos finales existentes se omiten. `--overwrite` permite descargarlos de nuevo.

El script usa únicamente la biblioteca estándar de Python y el
[catálogo público MITMA](https://mitma-movilidad-v2.s3.eu-west-1.amazonaws.com/?list-type=2).
No utiliza `config/datasets.json`, que contiene otro perfil y también fuentes INE.
No descarga el producto de agregados mensuales ni transforma los datos ni los carga en DuckLake.

## Organización local

```text
data/mitma/
  por-municipios/viajes/diarios/20230101_Viajes_municipios.csv.gz
  por-municipios/viajes/meses-completos/202301_Viajes_municipios.tar
  calidad/diarios/20230101_distritos_descartados.csv
  zonificación/...
```

Las mismas carpetas se utilizan para los otros niveles e indicadores. Se conservan las
rutas diarias del notebook `notebooks/00_lectura_datos.ipynb`. Para usar paquetes mensuales
en él hay que extraer previamente sus diarios a las carpetas `diarios/`, sin sobrescribir
archivos existentes. No se deben cargar a la vez diarios y copias extraídas del mismo mes.

## Si hay problemas

Las descargas son secuenciales, por bloques y con archivos temporales `.part`. El nombre
final solo aparece cuando el tamaño coincide con el catálogo. Hay hasta tres intentos
de conexión y hasta tres intentos de transferencia; no se reanudan archivos parciales.
No ejecutes dos descargas simultáneas sobre el mismo destino.

Repite el mismo comando tras un fallo: los archivos terminados se omitirán. Si un archivo
final existente está dañado, utiliza `--overwrite` (el archivo anterior se conserva hasta
completar su sustitución). La omisión por existencia no verifica su contenido ni detecta
revisiones publicadas por MITMA.

Un archivo no publicado se muestra como `ausente`, nunca se sustituye por otra fecha.
El resumen distingue descargados, omitidos, previstos (`--dry-run`), ausentes y fallidos.
El proceso termina con código 1 si hay ausencias o fallos, también en `--dry-run`.
Revisa los huecos de cobertura antes de pedir un año completo. Los TAR pueden ocupar varios
GB; consulta el volumen con `--dry-run` y reserva espacio adicional si vas a extraerlos.

La descarga no sustituye la validación y limpieza de Bronze/Silver. Las definiciones y
precauciones de lectura están en [el esquema MITMA](docs/esquema_datos_mitma.md).
