from app.utils.error_utils import error_response
from fastapi import APIRouter, Depends
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies import get_db
from app.schemas import SearchRequest

router = APIRouter()

@router.post("/search", response_model=dict)
def run_query(request: SearchRequest, db: Session = Depends(get_db)):
    pd_access = request.parameters.get("pd_access", False) if isinstance(request.parameters, dict) else False
    if not pd_access:
        return error_response(403, title="Unauthorized", detail=f"Unauthorized to PD")
    try:
        stmt = text(request.query)
        result = db.execute(stmt, request.parameters or [])
        rows = result.fetchall()
        data = [
            {**dict(row._mapping), "source": "AMP PD"}
            for row in rows
        ]
    except OperationalError as e:
        if "no such column" in str(e.orig):
            return error_response(
                400,
                title="Invalid Column",
                detail="The query references a column that is not available."
            )
        return error_response(
            400,
            title="Operational Error",
            detail=f"SQL error: {e.orig}"
        )
    except Exception as e:
        return error_response(400, title="Invalid SQL", detail=f"Invalid SQL: {e}")

    # Dynamically generate a data_model based on column names and types
    def infer_type(value):
        if isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        return "string"

    if data:
        first_row = data[0]
        data_model = {
            "type": "object",
            "properties": {
                key: {"type": infer_type(value)} for key, value in first_row.items()
            },
            "required": list(first_row.keys())
        }
    else:
        data_model = {"type": "object", "properties": {}}

    return {
        "data_model": data_model,
        "data": data,
        "pagination": {"next_page_url": None}
    }
