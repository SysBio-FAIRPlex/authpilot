from fastapi.responses import JSONResponse
from app.models.error import Error, ErrorList, ErrorResponse
from typing import Optional

def error_response(status_code: int, title: str, detail: Optional[str] = None, source: Optional[str] = None):
    error = Error(title=title, detail=detail, source=source)
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(errors=ErrorList([error])).model_dump()
    )
