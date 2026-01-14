from typing import Dict, Any
from pydantic import BaseModel

class ChatResponse(BaseModel):
    """Standard response format for chat endpoint"""
    answer: str
    sources: list[str] = []
