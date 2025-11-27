from typing import Optional

from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    message: str
    total_value: Optional[float] = None
    currency: Optional[str] = None
