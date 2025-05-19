from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class Table(BaseModel):
    name: str = Field(..., description="Uniquely identifies a table within this Data Connect service.")
    description: Optional[str] = Field(None, description="Optional description of the Table")
    data_model: Dict[str, Any] = Field(default_factory=dict)
    errors: Optional[List[Dict[str, Any]]] = None

class Pagination(BaseModel):
    next_page_url: Optional[str] = None

class ListTablesResponse(BaseModel):
    tables: List[Table]
    pagination: Optional[Pagination] = None
    errors: Optional[List[Dict[str, Any]]] = None
