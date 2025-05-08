from typing import List, Optional
from pydantic import BaseModel, RootModel

class Error(BaseModel):
    source: Optional[str] = None
    title: str
    detail: Optional[str] = None

class ErrorList(RootModel[List[Error]]):
    pass

class ErrorResponse(BaseModel):
    errors: ErrorList
