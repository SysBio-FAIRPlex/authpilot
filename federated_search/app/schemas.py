from pydantic import BaseModel
from typing import Optional

class SearchQueryRequest(BaseModel):
    sql: str
    pd_access: Optional[bool] = None
    ad_access: Optional[bool] = None
