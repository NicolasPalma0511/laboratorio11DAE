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
server = 'ec2-3-84-227-230.compute-1.amazonaws.com'
database = 'movielens'
username = 'SA'
password = 'YourStrong@Passw0rd'

conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "http://35.175.178.27:5124"}})

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
def recommend_movies_based_on_vote(voted_movie_id, user_ratings, movie_titles, top_n=3):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener las calificaciones de todos los usuarios para la película votada
    query = """
    SELECT r.user_id, r.movie_id, r.rating
    FROM ratings r
    WHERE r.movie_id = ?
    """
    cursor.execute(query, voted_movie_id)
    voted_movie_ratings = cursor.fetchall()
    
    user_ratings_for_voted_movie = {user_id: rating for user_id, _, rating in voted_movie_ratings}
    
    # Obtener las calificaciones de todos los usuarios para otras películas
    query = """
    SELECT r.user_id, r.movie_id, r.rating, m.title
    FROM ratings r
    JOIN movies m ON r.movie_id = m.movie_id
    WHERE r.movie_id != ?
    """
    cursor.execute(query, voted_movie_id)
    other_movie_ratings = cursor.fetchall()
    
    cursor.close()
    conn.close()

    # Crear un diccionario de calificaciones por usuario
    user_movie_ratings = {}
    for user_id, movie_id, rating, title in other_movie_ratings:
        if user_id not in user_movie_ratings:
            user_movie_ratings[user_id] = {}
        user_movie_ratings[user_id][movie_id] = rating
        if movie_id not in movie_titles:
            movie_titles[movie_id] = title

    # Calcular la distancia Manhattan entre las calificaciones de la película votada y otras películas
    movie_distances = {}
    for user_id, ratings in user_movie_ratings.items():
        if user_id in user_ratings_for_voted_movie:
            distance = manhattan_distance({voted_movie_id: user_ratings_for_voted_movie[user_id]}, ratings)
            for movie_id in ratings:
                if movie_id not in movie_distances:
                    movie_distances[movie_id] = 0
                movie_distances[movie_id] += distance

    # Obtener las películas con menor distancia (más similares)
    recommended_movies = sorted(movie_distances.items(), key=lambda x: x[1])[:top_n]
    recommendations = [(movie_id, movie_titles[movie_id]) for movie_id, _ in recommended_movies]
    
    return recommendations

@app.route("/", methods=["GET", "POST"])
def index():
    redis = get_redis()
    user1_id = request.form.get("user1_id")
    user2_id = request.form.get("user2_id")
    random_movies = get_random_movies()

    best_movies = []
    if user1_id and user2_id:
        user1_id = int(user1_id)
        user2_id = int(user2_id)
        ratings = get_movie_ratings(user1_id, user2_id)
        
        user1_ratings = {movie_id: rating for user_id, movie_id, rating, title in ratings if user_id == user1_id}
        user2_ratings = {movie_id: rating for user_id, movie_id, rating, title in ratings if user_id == user2_id}
        
        movie_titles = {movie_id: title for user_id, movie_id, rating, title in ratings}
        best_movies = get_best_movies(user1_ratings, user2_ratings, movie_titles)

    recommendations = []
    vote = None
    if request.method == "POST":
        vote = request.form.get("vote")
        if vote:
            vote = int(vote)
            redis.set('vote', vote)
            user_ratings = {user_id: {movie_id: rating for movie_id, rating in user_ratings.items()} for user_id, user_ratings in ratings.items()}
            movie_titles = {movie_id: title for movie_id, title in random_movies}
            recommendations = recommend_movies_based_on_vote(vote, user_ratings, movie_titles)
    
    return render_template("index.html", hostname=hostname, random_movies=random_movies, recommendations=recommendations, best_movies=best_movies, vote=vote)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
