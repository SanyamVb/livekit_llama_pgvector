from collections.abc import AsyncIterable

from dotenv import load_dotenv
from llama_index.core import (
    VectorStoreIndex,
)
from llama_index.core.llms import ChatMessage, MessageRole

from livekit.agents import Agent, llm
from livekit.agents.voice.agent import ModelSettings
from livekit.plugins import groq, openai, silero, google

load_dotenv()


class ChatEngineAgent(Agent):
    def __init__(self, index: VectorStoreIndex):
        super().__init__(
            instructions=(
                "You are a voice assistant created by LiveKit. If a user asks a query, search about the topic in the given index and find something relevant from there."
                " Your interface with users will be voice. You should use short and concise "
                "responses, and avoiding usage of unpronouncable punctuation."
            ),
            vad=silero.VAD.load(),
            stt=groq.STT(
                model="whisper-large-v3-turbo",
                language="en",
            ),
            llm=google.LLM(
                model="gemini-2.0-flash",
            ),
            tts = openai.TTS()
        )
        self.index = index
        self.query_engine = index.as_query_engine(vector_store_query_mode="hybrid", sparse_top_k = 5, similarity_top_k = 5)

    def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list[llm.FunctionTool],
        model_settings: ModelSettings,
    ) -> AsyncIterable[str]:
        user_msg = chat_ctx.items.pop()
        assert isinstance(user_msg, llm.ChatMessage) and user_msg.role == "user"
        user_query = user_msg.text_content
        assert user_query is not None

        llama_chat_messages = [
            ChatMessage(content=msg.text_content, role=MessageRole(msg.role))
            for msg in chat_ctx.items
            if isinstance(msg, llm.ChatMessage)
        ]
        stream = self.query_engine.query(user_query)
        # async for delta in stream.async_response_gen():
        print(stream)
        return stream
