from fastapi import FastAPI, HTTPException  # noqa
from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID
from datetime import datetime

from chatbot import ChatBot


class PromptModel(BaseModel):
    user_id: str
    role: Optional[Literal["student", "teacher"]] = None
    session_id: UUID
    prompt: str


class PromptResponseModel(BaseModel):
    user_id: str
    role: Optional[Literal["student", "teacher"]] = None
    session_id: UUID
    response: str
    timestamp: datetime


app = FastAPI()

# chatbot instantiation
bot = ChatBot().acompile()


@app.post('/chatbot')
async def chatbot(prompt_data: PromptModel):
    config = {"configurable": {
            "thread_id": prompt_data.session_id,
            "role": prompt_data.role
            }
        }
    response = await bot.ainvoke({"messages": prompt_data.prompt}, config)

    return {
        "user_id": prompt_data.user_id,
        "role": prompt_data.role,
        "response": (response["messages"][-1]).content,
        "timestamp": datetime.now()
        }


@app.get('/health-check')
async def healthcheck():
    return {
        "output": "Educify chatbot API is active!"
    }
