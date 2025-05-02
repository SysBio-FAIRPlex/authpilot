from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Person
from app.schemas import SearchQueryRequest
import httpx

router = APIRouter()

COLUMNS = [
    "person_id",
    "gender",
    "year_of_birth",
    "race",
    "ethnicity",
    "diagnosis_name"
]

# I'm arbitrarily choosing people with ID <= 1500 to be in PD,
# people with 1500 < ID <= 3000 to be in AD,
# and everyone above 3000 to be public
MAX_PD_ID = 1500
MAX_AD_ID = 3000

ROW_LIMIT = 10

@router.post("/search", response_model=dict)
async def run_query(body: SearchQueryRequest, db: Session = Depends(get_db)):
    query = db.query(Person)
    public_results = query.filter(Person.person_id > MAX_AD_ID).limit(ROW_LIMIT).all()
    public_data = [r.to_row() for r in public_results]

    pd_data = []
    ad_data = []
    sources = {"public": len(public_data)}

    async with httpx.AsyncClient() as client:
        if body.pd_access:
            try:
                pd_response = await client.post("http://amp-pd:8000/search", json=body.dict())
                pd_data = pd_response.json()["rows"]
                sources["pd"] = len(pd_data)
            except Exception as e:
                print(f"PD service error: {e}")
                sources["pd"] = 0

        if body.ad_access:
            try:
                ad_response = await client.post("http://amp-ad:8000/search", json=body.dict())
                ad_data = ad_response.json()["rows"]
                sources["ad"] = len(ad_data)
            except Exception as e:
                print(f"AD service error: {e}")
                sources["ad"] = 0

    combined_rows = public_data
    if body.pd_access:
        combined_rows = pd_data + combined_rows
    if body.ad_access:
        combined_rows = ad_data + combined_rows

    return {
        "columns": COLUMNS,
        "rows": combined_rows,
        "sources": sources
    }
