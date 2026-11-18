# SPRINT 1
## Zona

Vamos a usar como zona los distritos del MITMA. Esto es debido a dos factores:
- Es la unidad mínima del MITMA, lo que nos permitirá mantener los datos con más detalle del MITMA.
- Gracias a data/mitma/zonificación/relacion_ine_zonificacionMitma.csv podemos conocer la relación entre sección del INE y distrito del MITMA, que es una relación muchos a uno. Dado esto, los datos del INE en general deberán estar en función de la sección y tendremos que agregarlos a nivel de distrito de MITMA, definiendo una lógica diferente para cada columna, por ejemplo, para población será una suma y para renta será una media.

## Viajes y pernoctaciones

Dado que vamos a usar como zona los distritos del MITMA, vamos a quedarnos con los viajes y pernoctaciones únicamente a nivel de distrito. Como conocemos la relación que existe entre distritos, municipios y GAUs por el csv de arriba, en cualquier momento podemos calcular agregaciones a nivel de municipio y GAU.

## Tiempo

Los datos vienen de AEMET y son mediciones de estaciones meteorológicas para día. Para poder relacionar estas mediciones con la zonificación, lo que vamos a hacer es asignar cada zona a su estación más cercana. Esto tiene sentido dado el número elevado de estaciones meteorológicas. Lo malo de esto es que se puede asignar un distrito a una estación que está a una altitud muy diferente, lo que cambiaría bastante su climatología.

Otra opción es usar los datos de Copernicus, en concreto https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land-timeseries?tab=download, así tendríamos los datos a nivel horario y con una resolución de un grid de 9 km. Con la geometría de la zona podemos asignarle a cada zona a cada hora un valor para cada variable (temp, lluvia, nieve, viento). Estos datos son mucho más pesados.

## Vehiculos

Los datos vienen de datos.gob.es y son a nivel de municipio y año. Para asignarle un valor a cada zona podríamos darle un valor en función de la densidad de población, ya que esperamos una relación muy directa entre densidad de población y parque de vehículos.

## INE

Los datos son todos por secciones para luego poder hacer la agregación:

Datos ocupación: (los datos son 2021-2023)
https://ine.es/jaxiT3/Tabla.htm?t=70004&L=0

Datos población:
https://ine.es/dynt3/inebase/index.htm?padre=11555&capsel=11100

Datos income:
https://www.ine.es/jaxiT3/Tabla.htm?t=30824

Datos rama actividad: (los datos son 2021-2023)
https://ine.es/jaxiT3/Tabla.htm?t=70005&L=0

Datos nivel estudios: (Población de 15 y más años por sexo y nivel de estudios (agrupado))
https://ine.es/dynt3/inebase/index.htm?padre=10607&capsel=11676

Datos relación con la actividad: (Población de 16 y más años por país de nacimiento (España/extranjero) y relación con la actividad (agrupado))
https://ine.es/dynt3/inebase/index.htm?padre=10607&capsel=11676


# SPRINT 2

## MITMA

Ya tenemos script de ingestión.

## Vehículos

Ya tenemos script de ingestión.

## Tiempo

Ya tenemos script de ingestión.

## INE

No hay script de ingestión pero no parece muy difícil.