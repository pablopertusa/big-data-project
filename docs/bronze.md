# Bronze

**Notebook:** [01_bronze.ipynb](../notebooks/01_bronze.ipynb).  
**Fuente:** archivos locales en `data/mitma/`; especificaciones en `LEEME_Especificaciones_indicadores_OpenDataMovilidad.xlsx` (pestañas EB).

## Esquema

### Movilidad

```mermaid
%%{init: {'er': {'fontSize': 18}}}%%
erDiagram
    viajes {
        VARCHAR fecha
        VARCHAR periodo
        VARCHAR origen
        VARCHAR destino
        VARCHAR distancia
        VARCHAR actividad_origen
        VARCHAR actividad_destino
        VARCHAR estudio_origen_posible
        VARCHAR estudio_destino_posible
        VARCHAR residencia
        VARCHAR renta
        VARCHAR edad
        VARCHAR sexo
        VARCHAR viajes
        VARCHAR viajes_km
        VARCHAR _nivel
        VARCHAR _archivo
    }
    personas {
        VARCHAR fecha
        VARCHAR zona_pernoctacion
        VARCHAR edad
        VARCHAR sexo
        VARCHAR numero_viajes
        VARCHAR personas
        VARCHAR _nivel
        VARCHAR _archivo
    }
    pernoctaciones {
        VARCHAR fecha
        VARCHAR zona_residencia
        VARCHAR zona_pernoctacion
        VARCHAR personas
        VARCHAR _nivel
        VARCHAR _archivo
    }
```

### Catálogos de zonas y población

```mermaid
%%{init: {'er': {'fontSize': 18}}}%%
erDiagram
    nombres_zonas {
        VARCHAR ID
        VARCHAR name
        VARCHAR column0 "Solo municipios: indice original"
        VARCHAR _nivel
        VARCHAR _archivo
    }
    poblacion_zonas {
        VARCHAR column0 "Codigo de zona"
        VARCHAR column1 "Poblacion publicada"
        VARCHAR _nivel
        VARCHAR _archivo
    }
```

### Correspondencias y calidad

```mermaid
%%{init: {'er': {'fontSize': 18}}}%%
erDiagram
    correspondencias {
        VARCHAR seccion_ine
        VARCHAR distrito_ine
        VARCHAR municipio_ine
        VARCHAR distrito_mitma
        VARCHAR municipio_mitma
        VARCHAR gau_mitma
        VARCHAR _archivo
    }
    calidad_distritos {
        VARCHAR fecha
        VARCHAR zona
        VARCHAR _archivo
    }
```

### Geografía

```mermaid
%%{init: {'er': {'fontSize': 18}}}%%
erDiagram
    zonas_geograficas {
        BIGINT OGC_FID
        VARCHAR ID
        GEOMETRY geom
        VARCHAR _nivel
        VARCHAR _archivo
    }
    centroides {
        BIGINT OGC_FID
        VARCHAR ID
        GEOMETRY geom
        VARCHAR _nivel
        VARCHAR _archivo
    }
```

## Fichas de los conjuntos

| Vista / tabla | Procedencia relativa a `data/mitma/` | Qué representa una fila |
|---|---|---|
| `viajes` | `por-{nivel}/viajes/diarios/*.csv.gz` | Viajes expandidos de un día, periodo horario, OD y combinación de distancia, actividades, estudio posible, provincia de residencia, renta, edad y sexo. |
| `personas` | `por-{nivel}/personas/diarios/*.csv.gz` | Personas de un día y zona de pernoctación, por edad, sexo y categoría de número de viajes. |
| `pernoctaciones` | `por-{nivel}/pernoctaciones/diarios/*.csv.gz` | Personas de un día por zona de residencia y zona de pernoctación publicadas. |
| `nombres_zonas` | `zonificación/zonificacion_{nivel}/nombres_*.csv` | Código y nombre de una zona. La columna inicial sin nombre de municipios se conserva como `column0`; en otros niveles se añade NULL estructural. |
| `poblacion_zonas` | `zonificación/zonificacion_{nivel}/poblacion_*.csv` | Zona y población auxiliar. Sin cabecera: nombres técnicos `column0` y `column1`. |
| `correspondencias` | `zonificación/relacion_ine_zonificacionMitma.csv` | Combinación de códigos INE/MITMA. No asumir una sección INE única por fila. |
| `calidad_distritos` | `calidad/diarios/*.csv` | Distrito descartado por fecha según MITMA. No contiene un registro por cada distrito válido. |
| `zonas_geograficas` | `zonificación/zonificacion_{nivel}/zonificacion_*.shp`, sin centroides | Polígono de una zona de distritos, municipios o GAU. Geometría original en EPSG:3042. |
| `centroides` | `zonificación/zonificacion_{nivel}/*_centroides.shp` | Centroide publicado de una zona. Geometría original en EPSG:3042. |

### Significado de los campos de movilidad

- `periodo`: hora de inicio, de `00` a `23`; para viajes que entran en España, hora de entrada según las especificaciones.
- `origen`, `destino`, `zona_pernoctacion`: códigos territoriales; no son necesariamente códigos INE de municipio.
- `zona_residencia`: código publicado en pernoctaciones; su correspondencia territorial requiere atención (ver hallazgos).
- `distancia`: rango de distancia ortodrómica en km, no distancia exacta entre centroides.
- `actividad_origen/destino`: casa, trabajo/estudio, actividad frecuente o no frecuente.
- `estudio_*_posible`: etiqueta que indica si la actividad puede ser educativa; se conserva la grafía publicada.
- `residencia`: provincia de residencia en viajes, distinta de la zona de residencia de pernoctaciones.
- `renta`: rango de renta en miles de euros. `edad` y `sexo`: segmentos publicados, con `NA` por privacidad en viajes.
- `viajes`: estimación expandida, admite decimales. `viajes_km`: viajes multiplicados por distancia ortodrómica; en desplazamientos externos solo se contabiliza la distancia nacional.
- `numero_viajes`: categoría `0`, `1`, `2`, `2+`; esta última significa más de dos, no permite calcular un total exacto de viajes.
- `personas`: medida publicada con decimales; no es un recuento de identificadores individuales.
