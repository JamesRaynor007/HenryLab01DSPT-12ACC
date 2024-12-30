# <u> HENRY LAB 01 - MLOPS </u>
## <u> Proyecto Individual 01 </u>
![Portada](src/portada.gif)

Este repositorio es parte de la cohorte DS PT-12, elaborado por **Alejandro Castellano** como respuesta al proyecto individual requerido. <br>
Se trabaja sobre 2 (dos) datasets en formato .CSV, a partir de los cuales se deben realizar 6 (seis) funciones y luego un algoritmo de recomendación.<br>
A continuación detallo la estructura del repositorio y como se llevaron adelante las transformaciones y funciones necesarias.<br>

## <u>Los Datasets</u>
![Welcome](src/premios.jpg)

Los datasets **"movies_dataset"** y **"credits"** se basan en datos sobre películas, ambos datasets tienen diferentes estructuras y composición de datos.<br> 
**Movies** cuenta con información referida a las películas, como títulos, fecha de lanzamiento, compañias productoras, colecciones, lugares de filmación, etc.<br>
**Credits** por su parte contiene lo que hace a la película, lista de actores, lista de directores, géneros y más datos no relevantes a nuestro análisis.<br>

## <u>Breve EDA</u>
![Ahgghh](src/pareja4.jpg)
Los datos se encuentran con muchos inconvenientes, hay **duplicados, faltantes, vacíos, tipos incorrectos y hasta diccionarios y listas anidados**.<br>
En el <u>**archivo ETL + EDA**</u> se encontrarán las limpiezas realizadas, se eliminan duplicados, se cuentan vacíos y faltantes, se intentan ***homogenenizar los tipos*** acordes a las salidas esperadas.<br>
Los *primeros códigos se concentran en limpiar los datos*, eliminar columnas innecesarias y dejar un dataframe de partida lo más prolijo posible.<br>
Una vez logrado esto, se empieza a **particionar el dataset** base y se definen datasets específicos para las distintas funciones según sus requerimientos.<br>
Si usted desea utilizar el script ETL + EDA, asegúrese de tener en la misma carpeta los datasets y el mismo debiera ejecutarse por completo con una demora promedio de 20 minutos, arrojando como resultado los datasets definidos para cada función. <br>
**No consideré necesaria la utilización de gráficos por el estilo de datos y funciones requeridas.* <br>

## <u>Las Funciones</u>
![Hmmm](src/pensar.png)

**<u> Se definieron 6 (seis) funciones principales y 2 (dos) funciones accesorias </u>** :

* #### 1)<u> **Función 1:</u> Obtener el número acumulado de películas estrenadas en un mes [no importa el año].** <br><br>
* #### 2)<u> **Función 2:</u> Obtener el número acumulado de películas estrenadas en un día [no importa el año].**<br><br>
* #### 3)<u> **Función 3:</u> Obtener el score/puntuación de una película, su fecha de lanzamiento y voto promedio.**<br><br>
* #### 4)<u> **Función 4:</u> Obtener los votos obtenidos por una películas, si superan las 2.000 valoraciones, y su voto promedio.**<br><br>
* #### 5)<u> **Función 5:</u> Obtener el éxito de un actor, cantidad de películas protagonizadas, retorno promedio y ganancia bruta.**<br><br>
* #### <u> **Función 5 extra:</u> Obtener el listado de actores disponibles para consultar.**<br><br>
* #### 6)<u> **Función 6:</u> Obtener el éxito de un director, cantidad de películas dirigidas, retorno promedio y**
  #### **el listado de películas dirigidas con sus detalles de presupuesto, ganancia y retorno.**<br><br>
* #### <u> **Función 6 extra:</u> Obtener el listado de directores disponibles para consultar.**<br>
<br>

## <u>El Algoritmo</u>
![Hmmm](src/what.png)

La parte más díficil es elegir una película, por lo que necesitamos **definir un buen algoritmo** de recomendación.<br>
En este caso, teniendo muchas alternativas, y habiendo probado otras tantas, *me decanté por las basadas en palabras*, al **estilo bag of words**.<br>
Una columna del dataset original cuenta con un paneo general de la trama de cada película, al título de **"overview". Esta columna es el pilar del análisis**.<br>
Se procesa en el script aplicando **técnicas de preprocesamiento** para normalizar el texto, lo que implicó eliminar carácteres extraños, números, mayúsculas y **aplicar stemming** (porque resultó funcionar mejor que lemmatization). Una vez obtenida la columna preprocesada, **se tokeniza y recuentan las palabras**.<br>
*Estas palabras resultan ser más de 13 millones para cerca de 45.300 películas, rondando un promedio de 289 palabras por película, lo que arrojaba errores de memoria por la necesidad de crear matrices muy grandes (aplicando TF-IDF)*.<br>
Para lo cual, **la solución propuesta y aplicada fue reducir la cantidad de palabras a 100**, las 100 más comunes en la instancia de cada película (en caso de contener más de 100 originalmente).<br>
El resultado aplicado el filtro, nos da cerca de 1.1 millones de palabras, **<u>siendo una reducción de un 90%</u>**, la aplicación de la matriz TF-IDF se puede utilizar y el resultado fue convincente para mí como data engineer a cargo del desarrollo.<br>
* *Las películas analizadas principalmente fueron Titanic, Toy Story, Mortal Kombat y The President*.<br>
Siendo que para Toy Story recomienda Toy Story 2 y Toy Story 3, me pareció acertado.<br>
Siendo que para Mortal Kombat recomienda otras dos películas de Mortal Kombat, también me pareció acertado.<br>
Siendo que para Titanic recomienda 1900, una película basada en una historia de navegación e historia, también me pareció acertado.<br>

Debo mencionar que **su ordenamiento se da por el voto promedio** (vote_average según nombre de columna) y no seguí la recomendación de justamente, recomendar películas con cierta correlación con el voto promedio. Por ejemplo, Mortal Kombat recomienda una película de Mortal Kombat con valoración promedio 10 y otra con valoración promedio 3,8.<br>
<br>

# A disfrutar la mejor recomendación
![Ejemplo de Imagen](src/publico3.jpg)

A fin de cuentas, que algoritmo acierta con sus 5 recomendaciones? Con que una sea viable, el resto será disfrutar.

# <u> Saludos y Agradecimiento</u>
#### **A Henry y a todo/a lector/a interesado en este repositorio**. # Gracias

