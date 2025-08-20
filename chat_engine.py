from pathlib import Path
from dotenv import load_dotenv


from livekit.agents import AgentSession, AutoSubscribe, JobContext, WorkerOptions, cli
import nest_asyncio
from agents.chatengineagent import ChatEngineAgent
from init_db import init_db, upsert

db_name, url = init_db()
nest_asyncio.apply()
load_dotenv()

THIS_DIR = Path(__file__).parent
PERSIST_DIR = THIS_DIR / "chat-engine-storage"
DATA_FILE = THIS_DIR / "data" / "search_result.json"  # Assuming your JSON file is named 'data.json'

hybrid_index = upsert(DATA_FILE, db_name=db_name, url=url)

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    agent = ChatEngineAgent(hybrid_index)
    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    await session.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
