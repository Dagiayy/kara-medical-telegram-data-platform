from datetime import date, datetime

from pydantic import BaseModel


class TopProduct(BaseModel):
    product_name: str
    category: str | None = None
    mention_count: int


class ChannelActivity(BaseModel):
    date: date
    message_count: int


class SearchResult(BaseModel):
    message_id: str
    channel: str
    message_text: str | None = None
    sent_at: datetime | None = None


class TrendPoint(BaseModel):
    date: date
    message_count: int
    z_score: float


class HealthStatus(BaseModel):
    status: str
    database: str


class Paginated(BaseModel):
    limit: int
    offset: int
    count: int
