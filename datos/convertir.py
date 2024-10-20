import pandas as pd

base_path = './'

ratings = pd.read_csv(base_path + 'ratings.dat', delimiter='::', engine='python', header=None, 
                      names=['user_id', 'movie_id', 'rating', 'timestamp'])
ratings.to_csv(base_path + 'ratings.csv', index=False)

users = pd.read_csv(base_path + 'users.dat', delimiter='::', engine='python', header=None, 
                    names=['user_id', 'gender', 'age', 'occupation', 'zip_code'])
users.to_csv(base_path + 'users.csv', index=False)

movies = pd.read_csv(base_path + 'movies.dat', delimiter='::', engine='python', header=None, 
                     names=['movie_id', 'title', 'genres'], encoding='latin-1')
movies.to_csv(base_path + 'movies.csv', index=False)

print("Archivos .dat convertidos a .csv exitosamente.")
