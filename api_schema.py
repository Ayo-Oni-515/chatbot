from pydantic import BaseModel
from typing import Literal  # noqa
from uuid import UUID
from datetime import datetime


class PromptModel(BaseModel):
    user_id: str
    role: Literal["user", "service-provider"]
    session_id: UUID
    prompt: str


class PromptResponseModel(BaseModel):
    user_id: str
    role: Literal["user", "service-provider"]
    session_id: UUID
    prompt: str
    timestamp: datetime
