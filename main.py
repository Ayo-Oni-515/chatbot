from fastapi import FastAPI, HTTPException  # noqa
from pydantic import BaseModel
from typing import Literal
from uuid import UUID
from datetime import datetime

from chatbot import ChatBot


class PromptModel(BaseModel):
    user_id: str
    role: Literal["student", "teacher"]
    session_id: UUID
    prompt: str


class PromptResponseModel(BaseModel):
    user_id: str
    role: Literal["student", "teacher"]
    session_id: UUID
    prompt: str
    timestamp: datetime


app = FastAPI()

# chatbot instantiation
bot = ChatBot().acompile()


@app.post('/chatbot')
async def chatbot(prompt_data: PromptModel):
    config = {"configurable": {"thread_id": prompt_data.session_id}}
    response = await bot.ainvoke({"messages": prompt_data.prompt}, config)

    return {
        "user_id": prompt_data.user_id,
        "role": prompt_data.role,
        "response": (response["messages"][-1]).content
        }


@app.get('/health-check')
async def healthcheck():
    return {
        "output": "Chatbot API is active!"
    }
