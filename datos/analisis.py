import pyodbc
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la conexión a SQL Server en EC2
server = 'ec2-54-89-146-134.compute-1.amazonaws.com'
database = 'movielens'
username = 'SA'
password = 'YourStrong@Passw0rd'
connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# Conectarse a la base de datos
conn = pyodbc.connect(connection_string)

# Consultar los datos necesarios
query_data = 'SELECT * FROM u_data'
query_users = 'SELECT * FROM u_user'
query_items = 'SELECT * FROM u_item'

data_df = pd.read_sql(query_data, conn)
users_df = pd.read_sql(query_users, conn)
items_df = pd.read_sql(query_items, conn)

# Cerrar la conexión
conn.close()

# Renombrar las columnas para mayor claridad
data_df.columns = ['user_id', 'item_id', 'rating', 'timestamp']
users_df.columns = ['user_id', 'age', 'gender', 'occupation', 'zip_code']
items_df.columns = ['movie_id', 'movie_title', 'release_date', 'video_release_date', 'IMDb_URL'] + [f'genre_{i}' for i in range(19)]

# Análisis comparativo

# 1. Distribución de las calificaciones
plt.figure(figsize=(10,6))
sns.histplot(data_df['rating'], bins=5, kde=False, color='blue')
plt.title('Distribución de las calificaciones')
plt.xlabel('Calificación')
plt.ylabel('Cantidad de calificaciones')
plt.show()

# 2. Distribución de las edades de los usuarios
plt.figure(figsize=(10,6))
sns.histplot(users_df['age'], bins=20, kde=True, color='green')
plt.title('Distribución de edades de los usuarios')
plt.xlabel('Edad')
plt.ylabel('Cantidad de usuarios')
plt.show()

# 3. Promedio de calificaciones por película
avg_rating_per_movie = data_df.groupby('item_id')['rating'].mean().reset_index()
avg_rating_per_movie = avg_rating_per_movie.merge(items_df[['movie_id', 'movie_title']], left_on='item_id', right_on='movie_id')
top_10_movies = avg_rating_per_movie.sort_values(by='rating', ascending=False).head(10)

plt.figure(figsize=(10,6))
sns.barplot(x='rating', y='movie_title', data=top_10_movies, palette='viridis')
plt.title('Top 10 películas con mejores calificaciones promedio')
plt.xlabel('Calificación promedio')
plt.ylabel('Película')
plt.show()

# 4. Promedio de calificaciones por género
# Vamos a sumar todos los géneros por película
items_df['genres_sum'] = items_df.iloc[:, 5:].sum(axis=1)

# Hacemos un merge entre items y ratings para obtener los géneros
merged_df = pd.merge(data_df, items_df, left_on='item_id', right_on='movie_id')
average_genre_ratings = merged_df.groupby('genres_sum')['rating'].mean().reset_index()

plt.figure(figsize=(10,6))
sns.barplot(x='genres_sum', y='rating', data=average_genre_ratings, palette='plasma')
plt.title('Promedio de calificaciones por cantidad de géneros')
plt.xlabel('Cantidad de géneros en una película')
plt.ylabel('Calificación promedio')
plt.show()

# 5. Calificaciones promedio por ocupación
merged_users_ratings = pd.merge(data_df, users_df, on='user_id')
average_ratings_by_occupation = merged_users_ratings.groupby('occupation')['rating'].mean().reset_index()

plt.figure(figsize=(10,6))
sns.barplot(x='rating', y='occupation', data=average_ratings_by_occupation, palette='coolwarm')
plt.title('Promedio de calificaciones por ocupación')
plt.xlabel('Calificación promedio')
plt.ylabel('Ocupación')
plt.show()

