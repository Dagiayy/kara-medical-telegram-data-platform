# api/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class TopProduct(BaseModel):
    product_name: str
    mention_count: int

class ChannelActivity(BaseModel):
    date: str
    message_count: int

class SearchResult(BaseModel):
    message_id: int
    message_text: str
    timestamp: str
