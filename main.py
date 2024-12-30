# Importamos las librerías necesarias.
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles  
from pydantic import BaseModel
import pandas as pd
import os
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Se definen las rutas para acceder a los archivos, preferí utilizarlas de forma dinámica para no estar condicionado a una ruta específica que provocara rigidez.
# Definir la ruta a la carpeta "dataset", para mantener ordenado el repositorio.

dataset_path = os.path.join(os.path.dirname(__file__), 'datasets')

# Crear un diccionario para almacenar los DataFrames. Sugerencia de IA.
dataframes = {}

# Listar los archivos en la carpeta "dataset" y cargar solo los CSV.
for filename in os.listdir(dataset_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(dataset_path, filename)
        try:
            dataframes[filename] = pd.read_csv(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al cargar {filename}: {str(e)}")

# Se cargan los CSV y se definen los DataFrames a utilizar.
df_monthly = dataframes.get('01-PeliculasPorMes.csv')
df_daily = dataframes.get('02-PeliculasPorDia.csv')
scores_df = dataframes.get('03-FuncionScore.csv')
votes_df = dataframes.get('04-FuncionVotos.csv')
funcion_actor = dataframes.get('05-FuncionActor.csv')
resultado_cast_actores = dataframes.get('05-ResultadoCastActores.csv')
lista_actores = dataframes.get('05x-ListaActores.csv')
resultado_crew = dataframes.get('06-ResultadoCrew.csv')
funcion_director = dataframes.get('06-FuncionDirector.csv')
data = dataframes.get('07-DataReduction.csv')

# Un chequeo de que las columnas requeridas estén presentes en los archivos cargados.
for df, required_columns in [
    (df_monthly, ['title', 'month']),
    (df_daily, ['title', 'day_of_week']),
    (votes_df, ['title', 'vote_count', 'vote_average']),
    (scores_df, ['title', 'release_year', 'popularity']),
    (resultado_crew, ['movie_id', 'name']),
    (funcion_director, ['id', 'revenue', 'return']),
    (resultado_cast_actores, ['movie_id', 'name']),
    (funcion_actor, ['id', 'return']),
    (lista_actores, ['name']),
]:
    if not all(column in df.columns for column in required_columns):
        raise HTTPException(status_code=500, detail="El DataFrame no contiene las columnas esperadas.") #Un manejo de errores por si no se detecta una columna.

# Un pequeño diccionario de los meses, para recibir los datos en español y procesarlos en inglés como está el archivo.
meses_map = {
    'enero': 'January',
    'febrero': 'February',
    'marzo': 'March',
    'abril': 'April',
    'mayo': 'May',
    'junio': 'June',
    'julio': 'July',
    'agosto': 'August',
    'septiembre': 'September',
    'octubre': 'October',
    'noviembre': 'November',
    'diciembre': 'December'
}

# Igual que el anterior, solo que en este caso para los días.
dias_map = {
    'lunes': 'Monday',
    'martes': 'Tuesday',
    'miercoles': 'Wednesday',
    'jueves': 'Thursday',
    'viernes': 'Friday',
    'sabado': 'Saturday',
    'domingo': 'Sunday',
}

# Se definen clases para estructurar las respuestas a las consultas de Actor, Director y Peliculas dirigidas.
class MessageResponse(BaseModel):
    mensaje: str

class MovieInfo(BaseModel):
    title: str
    release_date: str
    return_: str
    budget: str
    revenue: str

class DirectorResponse(BaseModel):
    resultado_texto: str
    movies: List[MovieInfo]

# Una de mis favoritas, hacer que las entradas no sean sensibles al uso de mayúsculas. Genera flexibilidad en el código.
df_monthly.columns = df_monthly.columns.str.lower()
df_daily.columns = df_daily.columns.str.lower()
votes_df.columns = votes_df.columns.str.lower()
scores_df.columns = scores_df.columns.str.lower()
resultado_crew.columns = resultado_crew.columns.str.lower()
funcion_director.columns = funcion_director.columns.str.lower()
resultado_cast_actores.columns = resultado_cast_actores.columns.str.lower()
funcion_actor.columns = funcion_actor.columns.str.lower()
lista_actores.columns = lista_actores.columns.str.lower()

# Inicializar el vectorizador y calcular la matriz TF-IDF. Aquí tuve inconvenientes para iniciarlo luego de definir la api, por eso quedó antes de definir la misma.
tfidf_vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf_vectorizer.fit_transform(data['TokensLista'])

#Se inicia la API.
app = FastAPI(
    title="API de Películas",
    description="Esta API permite consultar información sobre películas, sus votaciones, puntuaciones, directores y actores.",
    version="1.0.0",
)

# Montar la carpeta 'images' para servir archivos estáticos, adicional con fines estéticos.
app.mount("/images", StaticFiles(directory="images"), name="images")

#Le dedico un mensaje de bienvenida, junto con las explicaciones de las funciones y les proveo ejemplos de uso y links para comprobar funcionalidad.
@app.get("/", response_class=HTMLResponse)      #Me pareció que el formato original era muy básico y que podía mejorarlo, así que investigué y HTML resultó útil y afín.
async def read_root(request: Request):
    base_url = str(request.url).rstrip('/')     #Utilizo una URL dinámica a fin de que los ejemplos sigan el host, sea local o una plataforma.
    return f"""
    <html>
        <head>
            <title>Bienvenido a la API de Películas</title>
            <style>
                body {{
                    background-image: url('/images/cinev2.jpg');
                    background-size: cover; /* Cubre todo el fondo */
                    background-position: center; /* Centra la imagen */
                    color: white; /* Cambia el color del texto para que sea más legible */
                }}
            </style>
        </head>
        <body>
            <h1>Bienvenido a la API de películas de Ale.</h1>
            <h2>Instrucciones:</h2>
            <p>Utiliza los siguientes endpoints para interactuar:</p>
            <ul style="background-color: rgba(71, 53, 53, 0.7); width: 51%; padding: 10px; border-radius: 5px; list-style-type: none;">
                <li><code>/peliculas/mes/?mes=nombre_del_mes</code>: cantidad de películas estrenadas en un mes (desde 1874 hasta 2020).</li>
                <li><code>/peliculas/dia/?dia=nombre_del_dia</code>: cantidad de películas estrenadas en un día (desde 1874 hasta 2020).</li>
                <li><code>/votes/?title=nombre_pelicula</code>: valoraciones de una película y valoración promedio.</li>
                <li><code>/score/?title=nombre_pelicula</code>: popularidad y año de estreno de una película.</li>
                <li><code>/titles/</code>: títulos disponibles para consultar.</li>
                <li><code>/actor/{{actor_name}}</code>: actuaciones de un actor, retorno, promedio.</li>
                <li><code>/listar_actores</code>: actores disponibles para consultar.</li>
                <li><code>/director/{{director_name}}</code>: éxito de un director, ganancias de sus películas y más.</li>
                <li><code>/listar_directores</code>: directores disponibles para consultar.</li>
                <li><code>/recomendacion/?title={{tu_titulo}}</code>: recomendaciones de películas.</li>
        </ul>
    <h2>Links Ejemplo:</h2>
        <body>
            <ul style="background-color: rgba(71, 53, 53, 0.7); width: 23%; padding: 10px; border-radius: 5px; list-style-type: none;">
                <li><a href="{base_url}/peliculas/mes/?mes={list(meses_map.keys())[0]}">Para Mes: {list(meses_map.keys())[0]}</a></li>
                <li><a href="{base_url}/peliculas/dia/?dia={list(dias_map.keys())[0]}">Para Día: {list(dias_map.keys())[0]}</a></li>
                <li><a href="{base_url}/score/?title=Toy%20Story">Para Puntuación: Toy Story</a></li>
                <li><a href="{base_url}/votes/?title=Inception">Para Votación: Inception</a></li>
                <li><a href="{base_url}/titles/">Para Títulos</a></li>
                <li><a href="{base_url}/actor/Leonardo%20DiCaprio">Para Información del Actor: Leonardo DiCaprio</a></li>
                <li><a href="{base_url}/listar_actores">Para Todos los Actores</a></li>
                <li><a href="{base_url}/director/Quentin%20Tarantino">Para Información del Director: Quentin Tarantino</a></li>
                <li><a href="{base_url}/directores">Para Todos los Directores</a></li>
                <li><a href="{base_url}/recomendacion/?title=Inception">Para Recomendaciones</a></li>
            </ul>
        </body>
    </html>
            """

#Se define la primer funcionalidad con el nombre cantidad_filmaciones_mes.
@app.get("/peliculas/mes/", response_class=HTMLResponse)
def cantidad_filmaciones_mes(mes: str):
    mes = mes.lower()              
    if mes not in meses_map:
        raise HTTPException(status_code=400, detail="Mes no válido. Por favor ingrese un mes en español.")

    mes_en_ingles = meses_map[mes]
    resultado = df_monthly[df_monthly['month'] == mes_en_ingles]
    cantidad = resultado['title'].count() if not resultado.empty else 0

    # Agregar HTML para la imagen
    return HTMLResponse(content=f"""
    <div>
            <div style="background-color: rgb(16, 130, 122); height: 100vh; padding: 20px;">
                <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;">
            La cantidad de películas que fueron estrenadas en el mes de <strong>{mes_en_ingles}</strong> es: <strong>{cantidad}</strong>.
            </p>
            <img src="/images/cinta3.jpg" alt="Cinta" style="width:100%; max-width:600px;"/>
        </div>
    </div>
    """)


#Se define la segunda funcionalidad con el nombre cantidad_filmaciones_dia.
@app.get("/peliculas/dia/", response_class=HTMLResponse)
def cantidad_filmaciones_dia(dia: str):
    dia = dia.lower()
    if dia not in dias_map:
        raise HTTPException(status_code=400, detail="Día no válido. Por favor ingrese un día en español.")

    dia_en_ingles = dias_map[dia]
    cantidad = df_daily[df_daily['day_of_week'] == dia_en_ingles].shape[0]

    # Agregar HTML para la imagen
    return HTMLResponse(content=f"""
    <div>
        <div style="background-color: rgb(16, 130, 122); height: 100vh; padding: 20px;">
        <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;">
        La cantidad de películas que fueron estrenadas en el día <strong>{dia_en_ingles}</strong> es: <strong>{cantidad}</strong>.
        </p>
        <img src="/images/cinta2.jpg" alt="Cinta" style="width:100%; max-width:600px;"/>
    </div>
    """)

#Se define la tercera funcionalidad con el nombre score_titulo.
@app.get("/score/", response_class=HTMLResponse)
async def score_titulo(title: str):
    movie = scores_df[scores_df['title'].str.lower() == title.lower()]
    if movie.empty:
        raise HTTPException(status_code=404, detail="Película no encontrada.")
    
    movie_data = movie.iloc[0]
    
    # Crear contenido HTML para la respuesta
    response_content = f"""
    <div>
        <div style="background-color: rgb(16, 130, 122); height: 100vh; padding: 20px;">
        <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;">
        La película '<strong>{movie_data['title']}</strong>' fue estrenada en el año <strong>{int(movie_data['release_year'])}</strong>, con una popularidad de <strong>{float(movie_data['popularity']):.2f}</strong>.
        </p>
        <img src="/images/pareja4.jpg" alt="Pareja" style="width:100%; max-width:600px;"/>
    </div>
    """
    
    return HTMLResponse(content=response_content)

#Se agrega una funcionalidad titles, para que el usuario pueda listar los titulos disponibles para consultar. 
#No es requerido, puede ocasionar perdida de eficiencia, pero lo considero útil. Tiene un delay de respuesta de entre 15-20 segundos.
@app.get("/titles/", response_class=HTMLResponse)
def get_titles():
    Titulos = votes_df['title'].unique().tolist()
    titulos_html = "<ul>"
    for titulo in Titulos:
        titulos_html += f"<li>{titulo}</li>"
    titulos_html += "</ul>"
    
    # HTML para la imagen fija a la derecha
    return HTMLResponse(content=f"""
        <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        color: white; /* Color del texto del cuerpo */
                        background-color: rgb(16, 130, 122); /* Color de fondo del cuerpo */
                        height: 100vh; /* Altura completa de la ventana */
                        margin: 0; /* Quitar margen por defecto */
                        padding: 20px; /* Espaciado interno */
                    }}
                    h2 {{
                        color: black; /* Color del título */
                    }}
                    .fixed-image {{
                        position: fixed;
                        top: 20px; /* Ajusta la posición vertical */
                        right: 20px; /* Ajusta la posición horizontal */
                        width: 450px; /* Ajusta el tamaño de la imagen */
                    }}
                </style>
            </head>
            <body>
                <h2><u>Titulos disponibles: (esperar 20 segundos para explorar)</u></h2>
                {titulos_html}
                <img src="/images/cinta4.jpg" alt="Cinta" class="fixed-image"/>
            </body>
        </html>
    """)


#Se define la cuarta funcionalidad con el nombre votos_titulo.
@app.get("/votes/", response_class=HTMLResponse)
async def votos_titulo(title: str):
    movie = votes_df[votes_df['title'].str.lower() == title.lower()]
    if movie.empty:
        raise HTTPException(status_code=404, detail="Película no encontrada.")
    
    movie_data = movie.iloc[0]
    if movie_data['vote_count'] < 2000:
        return HTMLResponse(content=f"""
        <html>
            <head>
                <style>
                    body {{
                        background-color:rgb(16, 130, 122); /* Cambia este color por el que desees */
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                    }}
                </style>
            </head>
            <body>
                <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;"
                La película '<strong>{movie_data['title']}</strong>' tuvo menos de 2000 valoraciones.
                </p>
            </body>
        </html>
        """)  # Requisito de consigna, si no cumple con la condición, devuelve mensaje.
    else:
        response_content = f"""
        <html>
            <head>
                <style>
                    body {{
                        background-color:rgb(16, 130, 122); /* Cambia este color por el que desees */
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                    }}
                </style>
            </head>
            <body>
                <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;"
                La película '<strong>{movie_data['title']}</strong>' tuvo <strong>{int(movie_data['vote_count'])}</strong> votos y su puntaje promedio fue <strong>{float(movie_data['vote_average']):.2f}.</strong>
                </p>
                <img src="/images/publico1.jpg" alt="Público" style="width:100%; max-width:600px;"/>
            </body>
        </html>
        """
        return HTMLResponse(content=response_content)

#Se define la quinta funcionalidad con el nombre get_actor
@app.get("/actor/{actor_name}", response_class=HTMLResponse)
def get_actor(actor_name: str):
    if not actor_name:
        raise HTTPException(status_code=400, detail="El nombre del actor no puede estar vacío.")
    
    actor_name_normalizado = actor_name.lower()
    peliculas_actor = resultado_cast_actores[resultado_cast_actores['name'].str.lower() == actor_name_normalizado]

    if peliculas_actor.empty:
        raise HTTPException(status_code=404, detail="Actor no encontrado")

    movie_ids = peliculas_actor['movie_id'].tolist()                                #crea una lista con los id de las peliculas en las que se encuentra el actor.
    ganancias_actor = funcion_actor[funcion_actor['id'].isin(movie_ids)]            #crea otra lista para evaluar las ganancias del actor.

    retorno_total = ganancias_actor['return'].sum()                                 #suma el total de ganancias (revenue) de las peliculas en las que actuó.
    ganancias_validas = ganancias_actor[ganancias_actor['return'] > 0]              #distingo aquellas peliculas que tuvieron ganancias (revenue) de las que no. 
    cantidad_peliculas_validas = len(ganancias_validas)                             #válido el total de peliculas con ganancias.

    if cantidad_peliculas_validas > 0:                                              #si tiene peliculas con ganancias,
        retorno_promedio = round(ganancias_validas['return'].mean(), 2) * 100       #calculará el promedio.
    else:
        retorno_promedio = 0.0                                                      #caso contrario, será 0.

    retorno_total_formateado = f"{retorno_total * 100:,.2f}%"                       #se utilizan formatos con porcentajes para prolijidad de la salida.
    retorno_promedio_formateado = f"{retorno_promedio:,.2f}%"

    peliculas_con_return_zero = ganancias_actor[ganancias_actor['return'] == 0]['id'].tolist()      #distingo las peliculas que tuvieron ganancias(revenue) = 0.
    peliculas_con_return_zero_count = len(peliculas_con_return_zero)                                ##cuento las peliculas con ganancias (revenue) = 0.

    # Una salida en texto ordenado para facilitar interpretación.
    resultado_texto = (
        f"El actor <strong>{actor_name}</strong> ha actuado en <strong>{len(ganancias_actor)}</strong> películas, "                 #Nombre de actor y cantidad total de peliculas .
        f"con un retorno total de <strong>{retorno_total_formateado}</strong>, "                                                    #Ganancias totales del actor.
        f"y un retorno promedio de <strong>{retorno_promedio_formateado}</strong>. "                                                #Promedio de ganancias sobre peliculas con ganancias (revenue).
        f"La cantidad de películas sin retorno en el dataset son <strong>{peliculas_con_return_zero_count}</strong>, "              #Cantidad de peliculas con ganancias(revenue) = 0.
        f"el retorno promedio contándolas es de <strong>{round(retorno_total / len(ganancias_actor) * 100, 2):,.2f}%</strong>."     #Retorno promedio total, sobre total de peliculas.
    )                                                                                                                               #Me pareció importante distinguir los promedios, y la consigna no lo aclaraba pero es información útil.

    # Incluir HTML para la imagen
    return HTMLResponse(content=f"""
    <div style="background-color: rgb(16, 130, 122); height: 100vh; padding: 20px;">
        <div style="display: flex; justify-content: space-between; max-width: 80%; margin: auto;">
            <div style="flex: 1; max-width: 50%;">
                <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;">
                    {resultado_texto}
                </p>
            </div>
            <img src="/images/oscar2.jpg" alt="Oscar" style="width: 60%; max-width: 500px;"/>
        </div>
    </div>
    """)

#Funcionalidad extra: permite listar los actores que se pueden consultar. También tiene delay de entre 20-30 segundos.
@app.get("/listar_actores", response_class=HTMLResponse)
def listar_actores():
    actores_lista = lista_actores['name'].tolist()  
    actores_html = "<ul>"
    for actor in actores_lista:
        actores_html += f"<li>{actor}</li>"
    actores_html += "</ul>"
    return HTMLResponse(content=f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: black; /* Color de texto por defecto */
                    background-image: url('/images/alfombraroja.jpg'); /* Ruta de tu imagen de fondo */
                    background-size: cover; /* Ajusta el tamaño de la imagen para cubrir el fondo */
                    background-attachment: fixed; /* Mantiene la imagen fija al hacer scroll */
                    background-position: center; /* Centra la imagen */
                    margin: 0; /* Elimina los márgenes del body */
                }}
                h2 {{
                    position: fixed; /* Mantiene el título fijo en la pantalla */
                    margin-top: 10px; /* Ajusta el margen superior para el título */
                    color: white; /* Cambia el color del título a blanco */
                    text-align: left; 
                    background: rgba(0, 0, 0, 0.5); /* Fondo semitransparente para mejorar la legibilidad */
                    border-radius: 5px; /* Bordes redondeados */
                }}
                .actores-list {{
                    color: white; /* Cambia el color de la lista a blanco */
                    text-align: center; /* Centra la lista */
                }}
                .actores-list li {{
                    margin-top: 500px; /* Ajusta el margen superior para el listado */
                    display: block; /* Muestra los elementos de la lista en línea */
                    margin: 10px; /* Espacio entre los elementos de la lista */
                }}
            </style>
        </head>
        <body>
            <h2><u>Actores disponibles: <br> 
            (esperar 30 segundos para explorar) </u></h2>
            <ul class="actores-list">
                {actores_html}
            </ul>
        </body>
    </html>
    """)

#Se define la sexta funcionalidad con el nombre get_director
@app.get("/director/{director_name}", response_class=HTMLResponse)
def get_director(director_name: str):
    director_name_lower = director_name.lower()                                                         #Como toda función, inicia con la eliminación de susceptibilidad a mayúsculas.
    director_movies = resultado_crew[resultado_crew['name'].str.lower() == director_name_lower]         #Filtra el dataset con el nombre del director.

    if director_movies.empty:
        raise HTTPException(status_code=404, detail="Director no encontrado")                           #Manejo de errores.

    director_movies = director_movies.merge(funcion_director, left_on='movie_id', right_on='id', how='inner')   #Realiza un join para obtener los datos requeridos a consultar.

    total_revenue = director_movies['revenue'].sum()                                                            #Totalizo las ganancias (revenue).
    total_return = director_movies['return'].sum()                                                              #Totalizo el retorno (revenue/budget).
    average_return = total_return / len(director_movies) if len(director_movies) > 0 else 0                     #Calculo el retorno promedio.

    non_zero_returns = director_movies[director_movies['return'] > 0]                                           #Distingo película con retorno distinto a cero.
    average_return_non_zero = non_zero_returns['return'].mean() if len(non_zero_returns) > 0 else 0             #Calculo el retorno promedio sin considerar las películas con retorno cero.

    total_movies = len(director_movies)                                                                         #Cuento el total de películas que dirigió.
    zero_return_movies = director_movies[director_movies['return'] == 0]                                        #Filtro las películas que dirigió con retorno igual a cero.
    total_zero_return = len(zero_return_movies)                                                                 #Cuento el total de películas que dirigió con retorno igual a cero.

    # Generar la lista de información de las películas
    movies_info = [
        {
            "title": row['title'],                                      #Título.
            "release_date": row['release_date'],                        #Fecha de Estreno.
            "return": f"{row['return']:.2f}%",                          #Retorno, con estilo porcentaje.
            "budget": f"${row['budget']:,.2f}",                         #Presupuesto con estilo moneda.
            "revenue": f"${row['revenue']:,.2f}"                        #Ganancia con estilo moneda.
        } for index, row in director_movies.iterrows()                  
    ]

    # Generar el texto descriptivo
    resultado_texto = (
        f"El director <strong>{director_name}</strong> ha obtenido una ganancia total de <strong>${total_revenue:,.2f}</strong>, "                   #Nombre Director con ganancia total.
        f"con un retorno total promedio de <strong>{average_return:.2f}%</strong> en un total de <strong>{total_movies}</strong> películas, "       #Mención retorno promedio general.
        f"y con un retorno de <strong>{average_return_non_zero:.2f}%</strong> sin contar las "                                                      #Mención retorno específico películas con retorno distinto a cero.
        f"películas que no tienen retorno en este dataset.<strong>({total_zero_return})</strong>"                                                                    #Mención películas que no tienen el dato de retorno o el mismo es cero.
    )

    
        # Generar la lista de películas
    movies_list = "<ul>"
    for movie in movies_info:
        movies_list += (
            f"<li><strong>{movie['title']}</strong> - <br>"
            f"Fecha de lanzamiento: {movie['release_date']}, <br>"
            f"Retorno: {movie['return']}, <br>"
            f"Costo: {movie['budget']}, <br>"
            f"Ganancia: {movie['revenue']}</li><br>"
        )
    movies_list += "</ul>"

    # Combinar el texto con la lista de películas
    full_content = f"<p>{resultado_texto}</p><h3>Películas dirigidas:</h3>{movies_list}"

    # Agregar HTML para la imagen a la derecha
    return HTMLResponse(content=f"""
    <div style="display: flex; justify-content: space-between; max-width: 85%; margin: auto;">
        <div style="flex: 1; max-width: 60%;">
            <div style="background-color: rgb(16, 130, 122); padding: 20px; /* Removí height: 100vh; */">
                <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;"
                    {full_content}
                </p>
            </div>
        </div>
        <img src="/images/popcorn.jpg" alt="Palomitas" style="width: 550px; height: 700px; margin-top: 40px;"/> 
    </div>
    """)

#Funcionalidad extra: obtener la lista de directores disponibles para consultar. Tiene delay de entre 10-15 segundos.
@app.get("/directores", response_class=HTMLResponse)
def listar_directores():
    directores = resultado_crew['name'].unique().tolist()
    directores_html = "<ul>"
    for director in directores:
        directores_html += f"<li>{director}</li>"
    directores_html += "</ul>"
    
    # HTML para la imagen fija a la derecha
    return HTMLResponse(content=f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: black;
                }}
                .fixed-image {{
                    position: fixed;
                    top: 20px; /* Ajusta la posición vertical */
                    right: 20px; /* Ajusta la posición horizontal */
                    width: 600px; /* Ajusta el tamaño de la imagen */
                }}
            </style>
        </head>
        <body>
            <h2><u>Directores disponibles: (esperar 15 segundos para explorar)</u></h2>
            <div style="background-color: rgb(16, 130, 122); height: full; padding: 20px;">
            {directores_html}
            <img src="/images/director.jpg" alt="Director" class="fixed-image"/>
        </body>
    </html>
    """)


#La función estrella, que debe hacer predicciones a modo de recomendaciones. La verdad es que utilicé varios modelos y decanté por este por ser posible procesar dada
#la capacidad de memoria que permite render en su plataforma digital gratis, a su vez velocidad de consulta y al menos 1 recomendación me parece altamente satisfactoria,
# lo que para una recomendación de película considero suficiente. Me basé consultando "Toy Story","Mortal Kombat","Titanic","The President" principalmente.

@app.get("/recomendacion/", response_class=HTMLResponse)
def recomendacion(title: str):
    titulo_ingresado = title.lower()                # Eliminar susceptibilidad a mayúsculas.
    
    # Convertir todos los títulos del dataset a minúsculas para la comparación
    data['lower_title'] = data['title'].str.lower() 

    # Verificar si la película ingresada existe en el dataset
    if titulo_ingresado not in data['lower_title'].values:
        raise HTTPException(status_code=404, detail="Movie not found")

    idx = data[data['lower_title'] == titulo_ingresado].index[0]
    # Calcular la similitud, la matríz fue definida al inicio del código, antes de empezar la API.
    cosine_similarities = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()

    # Obtener las recomendaciones
    recommendations_indices = cosine_similarities.argsort()[-6:-1][::-1]

    # Añadir la columna similaridad y ordenar de acuerdo al vote_average según consigna.
    recommendations = data.iloc[recommendations_indices]
    recommendations['similarity'] = cosine_similarities[recommendations_indices]
    recommendations = recommendations.sort_values(by='vote_average', ascending=False)

    recommendations_html = "<ul>"
    for _, row in recommendations.iterrows():
        recommendations_html += f"<li><strong>{row['title']}</strong> - Voto promedio: <strong>{row['vote_average']}</strong></li>"
    recommendations_html += "</ul>"

    return HTMLResponse(content=f"""
    <div style="background-color: rgb(16, 130, 122); height: 100vh; padding: 20px;">
        <div style="display: flex; flex-direction: column; align-items: center; max-width: 80%; margin: auto;">
            <div style="display: flex; justify-content: space-between; width: 100%;">
                <div style="flex: 1; max-width: 50%;">
                    <p style="background-color: rgba(255, 255, 255, 0.7); padding: 10px; border-radius: 5px;">
                        Recomendaciones basadas en '<strong>{title}</strong>': {recommendations_html}
                    </p>
                </div>
                <img src="/images/publico.jpg" alt="Público" style="width: 600px; height: auto; margin-left: 20px;"/>
            </div>
            <div style="margin-top: 20px; width: 100%; display: flex; justify-content: flex-start;">
                <div style="margin-left: auto;">
                    <img src="/images/publico3.jpg" alt="Público 3" style="width: 450px; height: auto;"/>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; width: 100%; margin-top:-400px; align-items: flex-start;">
                <img src="/images/pareja3.jpeg" alt="Pareja" style="width: 450px; height: 400px;"/>
            </div>
        </div>
    </div>
    """)





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
