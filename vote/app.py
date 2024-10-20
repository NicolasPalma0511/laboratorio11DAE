from flask import Flask, render_template, request, jsonify, make_response, g
from flask_cors import CORS
from redis import Redis
import os
import socket
import random
import pyodbc  # Para conexión a la base de datos

# Configuración de opciones
hostname = socket.gethostname()

# Configuración de la conexión a SQL Server
server = 'ec2-44-202-150-106.compute-1.amazonaws.com'
database = 'movielens'
username = 'SA'
password = 'YourStrong@Passw0rd'

conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5124"}})

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

def get_db_connection():
    conn = pyodbc.connect(conn_str)
    return conn

# Obtener las calificaciones de dos usuarios
def get_movie_ratings(user1_id, user2_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT r.user_id, r.movie_id, r.rating, m.title
    FROM ratings r
    JOIN movies m ON r.movie_id = m.movie_id
    WHERE r.user_id IN (?, ?)
    """
    cursor.execute(query, (user1_id, user2_id))
    ratings = cursor.fetchall()
    cursor.close()
    conn.close()
    return ratings

# Calcular la distancia Manhattan entre las calificaciones de dos usuarios
def manhattan_distance(user1_ratings, user2_ratings):
    distance = 0
    for movie_id in set(user1_ratings.keys()).intersection(set(user2_ratings.keys())):
        rating1 = user1_ratings.get(movie_id, 0)
        rating2 = user2_ratings.get(movie_id, 0)
        distance += abs(rating1 - rating2)
    return distance

# Obtener las mejores películas según las similitudes
def get_best_movies(user1_ratings, user2_ratings, movie_titles, top_n=3):
    movie_scores = []
    
    for movie_id in set(user1_ratings.keys()).intersection(set(user2_ratings.keys())):
        rating1 = user1_ratings[movie_id]
        rating2 = user2_ratings[movie_id]
        movie_scores.append((movie_id, rating1, rating2))

    distances = []
    for movie_id, rating1, rating2 in movie_scores:
        distance = abs(rating1 - rating2)
        distances.append((movie_id, distance))

    distances.sort(key=lambda x: x[1])
    best_movies = [(movie_id, movie_titles[movie_id]) for movie_id, _ in distances[:top_n]]
    return best_movies

# Obtener dos películas aleatorias para mostrar en el voto
def get_random_movies():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT TOP 2 movie_id, title FROM movies ORDER BY NEWID()"
    cursor.execute(query)
    movies = cursor.fetchall()
    cursor.close()
    conn.close()
    return movies

# Obtener las mejores películas basadas en el voto del usuario
def recommend_movies_based_on_vote(voted_movie_id, top_n=3):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = f"""
    SELECT TOP {top_n} m.movie_id, m.title
    FROM movies m
    JOIN ratings r ON m.movie_id = r.movie_id
    WHERE r.movie_id != ?  -- Excluir la película votada
    ORDER BY ABS(r.rating - (SELECT AVG(rating) FROM ratings WHERE movie_id = ?)) ASC
    """
    cursor.execute(query, (voted_movie_id, voted_movie_id))
    recommendations = cursor.fetchall()
    cursor.close()
    conn.close()
    return recommendations

# Nueva función para obtener el último voto desde Redis
def get_last_voted_movie():
    redis_client = get_redis()
    return redis_client.get('last_voted_movie')

# Modificado: almacena el voto en Redis
@app.route("/", methods=['POST', 'GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    if not voter_id:
        voter_id = hex(random.getrandbits(64))[2:-1]

    selected_movie = None
    recommendations = []

    if request.method == 'POST':
        vote = request.form['vote']  # Obtén el movie_id votado
        selected_movie = vote

        # Almacenar el ID del voto en Redis
        redis_client = get_redis()
        redis_client.set('last_voted_movie', selected_movie)

        # Obtener recomendaciones basadas en el voto
        recommendations = recommend_movies_based_on_vote(selected_movie)

    # Obtener dos películas aleatorias para mostrar en el voto
    random_movies = get_random_movies()

    # Obtener calificaciones de dos usuarios para la recomendación personalizada
    user1_id = 1  # Puedes cambiar este ID
    user2_id = 2  # Puedes cambiar este ID
    ratings = get_movie_ratings(user1_id, user2_id)
    
    user1_ratings = {}
    user2_ratings = {}
    movie_titles = {}

    for row in ratings:
        user_id, movie_id, rating, title = row
        if user_id == user1_id:
            user1_ratings[movie_id] = rating
        else:
            user2_ratings[movie_id] = rating
        movie_titles[movie_id] = title

    distance = manhattan_distance(user1_ratings, user2_ratings)
    best_movies = get_best_movies(user1_ratings, user2_ratings, movie_titles)

    resp = make_response(render_template(
        'index.html',
        random_movies=random_movies,
        selected_movie=selected_movie,
        hostname=hostname,
        vote=selected_movie,
        best_movies=best_movies,  # Pasar las mejores películas a la plantilla
        recommendations=recommendations  # Asegúrate de pasar las recomendaciones
    ))
    resp.set_cookie('voter_id', voter_id)
    return resp

# Nueva ruta para obtener las recomendaciones basadas en el último voto
@app.route("/api/recommendations", methods=['GET'])
def api_recommendations():
    last_voted_movie = get_last_voted_movie()

    if not last_voted_movie:
        return jsonify({'error': 'No se ha registrado un voto'}), 400

    # Obtener recomendaciones basadas en el último voto
    recommendations = recommend_movies_based_on_vote(last_voted_movie)

    return jsonify({
        'movies': [{'title': movie[1], 'movie_id': movie[0]} for movie in recommendations]
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
