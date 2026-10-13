from pydantic import BaseModel, Field, field_validator

from core.config import get_settings

SESSION_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


class ChatRequest(BaseModel):
    session_id: str | None = Field(default=None, pattern=SESSION_ID_PATTERN)
    message: str = Field(min_length=1, max_length=get_settings().api.max_message_length)

    @field_validator("message")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("message must not be empty")
        return value


class SourceOut(BaseModel):
    title: str
    type: str | None = None
    slug: str | None = None
    image_url: str | None = None
    snippet: str
    score: float


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[SourceOut] = []


class ErrorResponse(BaseModel):
    error: str
    message: str
