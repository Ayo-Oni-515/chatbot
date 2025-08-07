from fastapi import FastAPI, HTTPException  # noqa
from pydantic import BaseModel

from chatbot import ChatBot


class PromptModel(BaseModel):
    user_id: str
    prompt: str


app = FastAPI()

# chatbot instantiation
bot = ChatBot().acompile()


@app.post('/chatbot')
async def chatbot(prompt_data: PromptModel):
    config = {"configurable": {"thread_id": prompt_data.user_id}}
    response = await bot.ainvoke({"messages": prompt_data.prompt}, config)

    return {
        "user_id": prompt_data.user_id,
        "response": (response["messages"][-1]).content}


@app.get('/health-check')
async def healthcheck():
    return {
        "output": "Educify chatbot API is active!"
    }
