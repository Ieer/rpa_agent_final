from typing import Any

from pydantic import BaseModel


class RunRequest(BaseModel):
    rpa_name: str
    params: dict[str, Any] | None = None


class ChatSendRequest(BaseModel):
    message: str
    session_key: str | None = None


class EmbeddingTestRequest(BaseModel):
    input_text: str = "embedding connectivity test"


class Status:
    SUCCESS = "success"
    FAILED = "failed"
    NOT_FOUND = "not_found"
