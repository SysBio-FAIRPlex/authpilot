from pydantic import BaseModel
from typing import Union, Any, Dict, List, Optional

class SearchRequest(BaseModel):
    query: str
    parameters: Optional[Union[List[Any], Dict[str, Any]]] = None
