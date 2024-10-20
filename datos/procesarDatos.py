import pandas as pd
import pyodbc

# Configuración de conexión
server = 'ec2-34-239-134-46.compute-1.amazonaws.com'
database = 'movielens'
username = 'SA'
password = 'YourStrong@Passw0rd'

conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"

# Función para crear tablas
def crear_tablas():
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        try:
            # Crear tabla ratings
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ratings' AND xtype='U')
            CREATE TABLE ratings (
                user_id INT,
                movie_id INT,
                rating INT,
                timestamp BIGINT
            );
            """)

            # Crear tabla movies
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='movies' AND xtype='U')
            CREATE TABLE movies (
                movie_id INT PRIMARY KEY,
                movie_title NVARCHAR(255),
                release_date NVARCHAR(10),
                video_release_date NVARCHAR(10),
                IMDb_URL NVARCHAR(255),
                unknown BIT,
                Action BIT,
                Adventure BIT,
                Animation BIT,
                [Children's] BIT,
                Comedy BIT,
                Crime BIT,
                Documentary BIT,
                Drama BIT,
                Fantasy BIT,
                [Film-Noir] BIT,
                Horror BIT,
                Musical BIT,
                Mystery BIT,
                Romance BIT,
                Sci_Fi BIT,
                Thriller BIT,
                War BIT,
                Western BIT
            );
            """)

            # Crear tabla users
            cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
            CREATE TABLE users (
                user_id INT PRIMARY KEY,
                gender NVARCHAR(1),
                age INT,
                occupation INT,
                zip_code NVARCHAR(10)
            );
            """)

            conn.commit()  
            print("Tablas creadas exitosamente.")
        except Exception as e:
            print(f"Error creando las tablas: {e}")

# Función para cargar datos usando BULK INSERT
def cargar_csv_a_sql(csv_file, table_name):
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        try:
            bulk_insert_query = f"""
            BULK INSERT {table_name}
            FROM '{csv_file}'
            WITH (
                FIELDTERMINATOR = ',',  
                ROWTERMINATOR = '\\n',   
                FIRSTROW = 2             
            );
            """
            cursor.execute(bulk_insert_query)
            conn.commit()  
            print(f"Datos de {csv_file} cargados exitosamente en {table_name}.")
        except Exception as e:
            print(f"Error subiendo los datos de {csv_file} a {table_name}: {e}")

# Crear las tablas
crear_tablas()

# Definir los archivos CSV y sus tablas correspondientes
csv_files = {
    'C:/Users/Nicolas/Downloads/examen2/sqlserver/datos/ratings.csv': 'ratings',
    './movies.csv': 'movies',
    './users.csv': 'users'
}

# Cargar cada archivo CSV en su respectiva tabla
for csv_file, table_name in csv_files.items():
    cargar_csv_a_sql(csv_file, table_name)
