from pydantic import BaseModel
from datetime import date

class SearchQueryRequest(BaseModel):
    sql: str
