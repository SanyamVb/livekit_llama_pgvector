from pathlib import Path
from dotenv import load_dotenv
from llama_index.core import (
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
    Document
)

from livekit.agents import AgentSession, AutoSubscribe, JobContext, WorkerOptions, cli
import nest_asyncio
import json 
from agents.chatengineagent import ChatEngineAgent
from llama_index.vector_stores.postgres import PGVectorStore
from init_db import init_db

db_name, url = init_db()
nest_asyncio.apply()
load_dotenv()

THIS_DIR = Path(__file__).parent
PERSIST_DIR = THIS_DIR / "chat-engine-storage"
DATA_FILE = THIS_DIR / "data" / "search_result.json"  # Assuming your JSON file is named 'data.json'


if not PERSIST_DIR.exists():
    # Load the JSON data
    with open(DATA_FILE, 'r', encoding='utf-8') as file:
        json_data = json.load(file)
    for i in range(len(json_data)):
        json_data[i]['text'] = json_data[i]['text'] + json_data[i]['content_date']
    
    # Convert dictionaries to Document objects
    documents = [Document(**doc) for doc in json_data]

    hybrid_vector_store = PGVectorStore.from_params(
        database=db_name,
        host=url.host,
        password=url.password,
        port=url.port,
        user=url.username,
        table_name="bayers_livekit",
        embed_dim=1536,  # openai embedding dimension
        hybrid_search=True,
        text_search_config="english",
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )

    print(len(documents))
    for document in documents:
        # documents[i]['Text'] = documents[i]['Text'] + documents[i]['Content_Date']
        print(document)

    storage_context = StorageContext.from_defaults(
        vector_store=hybrid_vector_store
    )
    hybrid_index = VectorStoreIndex.from_documents(
        documents, storage_context=storage_context
    )
    # Store it for later
    # hybrid_index.storage_context.persist(persist_dir=PERSIST_DIR)
    # storage_context = StorageContext.from_defaults(
    #     docstore=SimpleDocumentStore.from_persist_dir(persist_dir="<persist_dir>"),
    #     vector_store=SimpleVectorStore.from_persist_dir(
    #         persist_dir="<persist_dir>"
    #     ),
    #     index_store=SimpleIndexStore.from_persist_dir(persist_dir="<persist_dir>"),
    # )
else:
    vector_store = PGVectorStore.from_params(
        database="vector_db",
        host="localhost",
        password="postgres",
        port=5432,
        user="postgres",
        table_name="data_bayers_livekit",
        embed_dim=1536,  # openai embedding dimension
        hybrid_search=True,
        text_search_config="english",
        hnsw_kwargs={
            "hnsw_m": 16,
            "hnsw_ef_construction": 64,
            "hnsw_ef_search": 40,
            "hnsw_dist_method": "vector_cosine_ops",
        },
    )
    # Load the existing index
    hybrid_index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    # hybrid_index = load_index_from_storage(storage_context)


async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    agent = ChatEngineAgent(hybrid_index)
    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    await session.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
