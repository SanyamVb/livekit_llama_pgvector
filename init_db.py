from sqlalchemy import make_url
import psycopg2

def init_db():

    connection_string = "postgresql://postgres:postgres@localhost:5432"
    db_name = "vector_db"
    conn = psycopg2.connect(connection_string)
    conn.autocommit = True

    with conn.cursor() as c:
        c.execute(f"DROP DATABASE IF EXISTS {db_name}")
        c.execute(f"CREATE DATABASE {db_name}")


    url = make_url(connection_string)
    return db_name, url
