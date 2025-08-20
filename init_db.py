from sqlalchemy import make_url
import psycopg2
from llama_index.vector_stores.postgres import PGVectorStore
import json 
from llama_index.core import (
    StorageContext,
    VectorStoreIndex,
    Document
)

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

def upsert(DATA_FILE, db_name, url, embed_dim = 1536):
    with open(DATA_FILE, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    for i in range(len(json_data)):
        json_data[i]['text'] = json_data[i]['text'] + " Date: " + json_data[i]['content_date']

    documents = [Document(**doc) for doc in json_data]

    hybrid_vector_store = PGVectorStore.from_params(
        database=db_name,
        host=url.host,
        password=url.password,
        port=url.port,
        user=url.username,
        table_name="bayers_livekit",
        embed_dim=embed_dim,  # openai embedding dimension
        hybrid_search=True,
        text_search_config="english",
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )

    storage_context = StorageContext.from_defaults(
        vector_store=hybrid_vector_store
    )
    hybrid_index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context
    )

    return hybrid_index
