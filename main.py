import asyncio
from contextlib import asynccontextmanager
import uuid
from fastapi import FastAPI, HTTPException  # noqa
from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID  # noqa
from datetime import datetime

from chatbot import ChatBot


class PromptModel(BaseModel):
    user_id: str
    role: Optional[Literal["student", "teacher"]] = None
    session_id: Optional[str] = None
    prompt: str


class PromptResponseModel(BaseModel):
    user_id: str
    role: Optional[Literal["student", "teacher"]] = None
    session_id: str
    response: str
    timestamp: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup logic
    async def session_cleanup_logic():
        while True:
            try:
                bot_init.memory.cleanup()
                # expired_length = bot_init.memory.cleanup()
                # remaining_session = bot_init.memory.get_active_sessions()
                # print(
                #     f"cleaned up {expired_length} expired session ids")
                # print(f"Remaining session: {remaining_session}")
            except Exception as e:
                # print(f"Error during cleanup: {e}")
                raise Exception(e.args)

            await asyncio.sleep(300)  # runs every 10 minutes(1800)

    cleanup_task = asyncio.create_task(session_cleanup_logic())

    try:
        yield  # Application runs here
    finally:
        # Shutdown logic
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            print("Cleanup task cancelled gracefully")


app = FastAPI(lifespan=lifespan)

# chatbot instantiation
bot_init = ChatBot()
bot = bot_init.acompile()


@app.post('/chatbot')
async def chatbot(prompt_data: PromptModel):
    if (prompt_data.session_id is None):
        # print(bot_init.memory.storage)

        prompt_data.session_id = str(uuid.uuid4())
        while prompt_data.session_id in bot_init.memory.storage:
            prompt_data.session_id = str(uuid.uuid4())
    elif (prompt_data.session_id not in bot_init.memory.storage):
        # print(bot_init.memory.storage)

        prompt_data.session_id = str(uuid.uuid4())
        while prompt_data.session_id in bot_init.memory.storage:
            prompt_data.session_id = str(uuid.uuid4())

    config = {"configurable": {
            "thread_id": prompt_data.session_id,
            "role": prompt_data.role
            }
        }
    response = await bot.ainvoke({"messages": prompt_data.prompt}, config)

    return {
        "user_id": prompt_data.user_id,
        "role": prompt_data.role,
        "session_id": prompt_data.session_id,
        "response": (response["messages"][-1]).content,
        "timestamp": datetime.now()
        }


@app.get('/health-check')
async def healthcheck():
    return {
        "output": "Educify chatbot API is active!"
    }
