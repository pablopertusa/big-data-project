# Silver: del dato de origen al distrito MITMA

Ejecutar `notebooks/silver.ipynb` después de [Bronze](bronze.md). El periodo de análisis es 2022–2024, ambos incluidos. El notebook reconstruye las tablas `silver` en DuckDB y escribe un CSV con cabecera por tabla en `data/silver/`. Para inspeccionarlos en una hoja de cálculo, importar los identificadores territoriales como **texto**: `01001` no es `1001`. Un campo numérico vacío indica ausencia de dato, no cero.

## Territorio, calendario y movilidad

| Tabla | Origen, unidad de cada fila y transformación |
|---|---|
| `zona` | Un distrito del catálogo MITMA. Se unen nombre, polígono y centroide por ID, y provincia y CCAA mediante la correspondencia territorial y el catálogo INE. El área del polígono proyectado se expresa en km². Sin atributos municipales. Las geometrías del CSV se exportan en WKT, EPSG:3042. |
| `agregaciones_zona` | Una combinación distinta de distrito, municipio **MITMA** y GAU de `mitma_relacion_ine`. Sirve para reagrupar movilidad; el municipio MITMA no es necesariamente el municipio administrativo INE usado por DGT. |
| `festivos` | Una fiesta por fecha y nombre. Se interpreta el calendario BOE de 2023 en orden: las cabeceras fijan el mes y las marcas de las columnas autonómicas indican el ámbito. Se deduplican fecha y nombre y se numeran en ese orden. |
| `relacion_festivos` | Un par fiesta–distrito: se unen las comunidades marcadas en el calendario con la CCAA de cada distrito. El alcance es autonómico; no incorpora fiestas municipales ni excepciones subautonómicas del BOE. |
| `viajes` | Una hora MITMA y par origen–destino. Se combinan `fecha` y `periodo` y se suman los viajes de todos los desgloses descartados. Se conserva la hora publicada, sin conversión de huso, y la medida fraccionaria del modelo de movilidad. |
| `mitma_pernoctaciones` | Un día y par residencia–pernoctación. La fuente ya viene a ese nivel; se tipan la fecha (medianoche del día de referencia) y la estimación decimal de personas. No es una serie horaria. |

## Correspondencia INE–MITMA y pesos de población

Se extraen los diez dígitos iniciales de `Secciones` y se enlazan con `seccion_ine` de `bronze.mitma_relacion_ine`. **La clave territorial que queda en Silver es `distrito_mitma` como `id_zona`.** Las filas nacionales, provinciales, municipales o sin sección enlazable no contribuyen. Se interpreta el punto como separador de miles y la coma como separador decimal. `año` es el 1 de enero del año de referencia.

| Tabla | Transformación por distrito y año |
|---|---|
| `poblacion` | Suma `ine_poblacion.Total` por sexo y lugar de nacimiento (España/extranjero). |
| `situacion_laboral` | Suma `ine_relacion_actividad.Total` por país de nacimiento agrupado y relación con la actividad. El universo es la población de 16 años o más. |
| `nivel_estudios` | Suma `ine_nivel_estudios.Total` por país de nacimiento agrupado y nivel de formación publicado. |
| `rama_actividad` | Suma `ine_rama_actividad.Total` por sexo y rama económica. El fichero incluye secciones para 2022 y 2023 dentro del periodo de análisis. |

Estas cuatro tablas conservan categorías de detalle: no se suman `Total` ni `Total CNAE` junto a sus componentes. Con cobertura parcial, una suma corresponde a las secciones y registros disponibles, no necesariamente a todo el distrito.

## Renta

`renta` reúne en una fila por distrito y año los cuatro indicadores de `ine_renta`: renta neta y bruta, por persona y por hogar. Para cada indicador se calcula `Σ(renta de sección × personas de sección) / Σ(personas de sección)` con las secciones enlazadas que tengan renta y un peso positivo del **mismo año**. El peso procede de `ine_poblacion`, seleccionando exclusivamente `Sexo = Total` y `Lugar de nacimiento = Total`, una vez por sección y año.

**Supuesto para renta por hogar:** no disponemos del número de hogares. Asumimos que hogares y personas son directamente proporcionales entre las secciones del distrito (tamaño medio de hogar comparable). Por eso usamos la población también para ponderar las dos rentas por hogar. Es una aproximación: si el tamaño medio de hogar difiere, el resultado puede no coincidir con la media que se obtendría ponderando por hogares reales. Si se incorpora ese denominador, sustituir los pesos solo para esos dos indicadores. Sin pares renta–peso utilizables, el valor queda nulo; no se toman pesos de otros años.

## Vehículos

`vehiculos` parte del censo de conductores y los seis indicadores de parque municipal de DGT, con año extraído del nombre del Excel. Cada municipio INE enlazado con un único distrito aporta allí su cifra íntegra. Si abarca varios distritos, se reparte cada medida según la población del mismo año de las secciones municipales de cada distrito. Solo se distribuye si hay población para todas las secciones del municipio en la correspondencia y el total es positivo: una muestra parcial no recibe el 100 % por accidente. Los municipios sin correspondencia no se asignan.

Para conservar enteros y el total municipal repartido, se toman las partes enteras de las cuotas y se asignan las unidades restantes por mayor resto (desempate por ID de distrito). Después se suman las contribuciones por distrito y año. `parque_total` se reparte como indicador propio: DGT incluye categorías adicionales a las cinco desglosadas.

## Meteorología

`meteorologia` conserva una fila por distrito y hora UTC de `copernicus_horario`, correspondiente al punto de rejilla del centroide. Se convierte temperatura de K a °C, precipitación y nieve de m a mm de agua equivalente y componentes de viento a velocidad en m/s mediante `√(u² + v²)`. Se conserva el periodo temporal de los valores de precipitación publicados, sin sumarlos entre horas. La columna `fecha` representa UTC; antes de cruzarla con movilidad hay que armonizar la referencia horaria.

Las precipitaciones negativas de origen se fijan en 0 mm en Silver; los valores ausentes siguen siendo nulos. Para consultar tipos y muestras de todas las tablas, ejecutar [`inspeccion_silver.ipynb`](../notebooks/inspeccion_silver.ipynb).
