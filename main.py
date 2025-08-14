from fastapi import FastAPI, HTTPException  # noqa
from chatbot import ChatBot
from datetime import datetime

from api_schema import PromptModel, PromptResponseModel  # noqa


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
        "response": (response["messages"][-1]).content,
        "timestamp": datetime.now()
        }


@app.get('/health-check')
async def healthcheck():
    return {
        "output": "Chaimbase chatbot API is active!"
    }
