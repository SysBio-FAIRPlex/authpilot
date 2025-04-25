from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Person
from app.schemas import SearchQueryRequest

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
def run_query(body: SearchQueryRequest, db: Session = Depends(get_db)):
    query = db.query(Person)

    pd_results = query.filter(Person.person_id <= MAX_PD_ID).limit(ROW_LIMIT).all()
    ad_results = query.filter(Person.person_id.between(MAX_PD_ID + 1, MAX_AD_ID)).limit(ROW_LIMIT).all()
    public_results = query.filter(Person.person_id > MAX_AD_ID).limit(ROW_LIMIT).all()

    pd_data = [r.to_row() for r in pd_results]
    ad_data = [r.to_row() for r in ad_results]
    public_data = [r.to_row() for r in public_results]

    if body.pd_access and body.ad_access:
        return {
            "columns": COLUMNS,
            "rows": pd_data + ad_data + public_data
        }
    elif body.pd_access:
        return {
            "columns": COLUMNS,
            "rows": pd_data + public_data
        }
    elif body.ad_access:
        return {
            "columns": COLUMNS,
            "rows": ad_data + public_data
        }
    else:
        return {
            "columns": COLUMNS,
            "rows": public_data
        }
