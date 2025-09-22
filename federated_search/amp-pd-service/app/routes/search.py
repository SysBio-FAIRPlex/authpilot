from app.utils.error_utils import error_response
from fastapi import APIRouter, Depends, Header
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies import get_db
from app.schemas import SearchRequest
from typing import Optional

router = APIRouter()

@router.post("/search", response_model=dict)
def run_query(request: SearchRequest, db: Session = Depends(get_db), authorization: Optional[str] = Header(None)):
    access_tier = "public"
    if isinstance(request.parameters, dict):
        access_tier = request.parameters.get("access_tier", "public")

    if access_tier in ["registered", "controlled"] and not authorization:
        access_tier = "public"

    # Define fields restricted by access tier
    restricted_fields = {}
    if access_tier == "public":
        restricted_fields = {
            "gender": "registered access only",
            "race": "registered access only",
            "ethnicity": "registered access only",
            "year_of_birth": "controlled access only"
        }
    elif access_tier == "registered":
        restricted_fields = {
            "year_of_birth": "controlled access only"
        }
    elif access_tier != "controlled":
        return error_response(400, title="Bad Request", detail="Invalid access_tier specified.")

    try:
        stmt = text(request.query)
        result = db.execute(stmt, request.parameters or [])
        rows = result.fetchall()
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

    # Remove restricted fields from the data rows
    data = []
    for row in rows:
        row_dict = dict(row._mapping)
        for field in restricted_fields:
            row_dict.pop(field, None)
        row_dict["source"] = "AMP PDRD"
        data.append(row_dict)

    # Build data_model from filtered data
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
        "restricted_fields": restricted_fields,
        "pagination": {"next_page_url": None}
    }
