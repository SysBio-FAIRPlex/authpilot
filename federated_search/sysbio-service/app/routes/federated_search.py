from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies import get_db
from app.models import Person
from app.schemas import SearchRequest
from dotenv import load_dotenv
import httpx
import os

load_dotenv()
AMP_PD_URL = os.getenv("AMP_PD_URL")
AMP_AD_URL = os.getenv("AMP_AD_URL")

router = APIRouter()

# I'm arbitrarily choosing people with ID <= 1500 to be in PD,
# people with 1500 < ID <= 3000 to be in AD,
# and everyone above 3000 to be public
MAX_PD_ID = 1500
MAX_AD_ID = 3000

ROW_LIMIT = 10

@router.post("/search", response_model=dict)
async def run_query(request: SearchRequest, db: Session = Depends(get_db)):
    pd_access = request.parameters.get("pd_access", False) if isinstance(request.parameters, dict) else False
    ad_access = request.parameters.get("ad_access", False) if isinstance(request.parameters, dict) else False

    try:
        stmt = text(request.query)
        result = db.execute(stmt, request.parameters or [])
        rows = result.fetchall()
        public_data = [dict(row._mapping) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid SQL: {e}")

    pd_data, ad_data = [], []
    sources = {"public": len(public_data)}

    async with httpx.AsyncClient() as client:
        if pd_access:
            try:
                pd_response = await client.post(f"{AMP_PD_URL}/search", json=request.dict())
                pd_data = pd_response.json()["data"]
                sources["pd"] = len(pd_data)
            except Exception as e:
                print(f"PD service error: {e}")
                sources["pd"] = 0

        if ad_access:
            try:
                ad_response = await client.post(f"{AMP_AD_URL}/search", json=request.dict())
                ad_data = ad_response.json()["data"]
                sources["ad"] = len(ad_data)
            except Exception as e:
                print(f"AD service error: {e}")
                sources["ad"] = 0

    all_data = public_data + pd_data + ad_data

    # Generate data_model schema from the first row
    def infer_type(value):
        if isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, bool):
            return "boolean"
        return "string"

    if all_data:
        first_row = all_data[0]
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
        "data": all_data,
        "sources": sources,
        "pagination": {"next_page_url": None}
    }
