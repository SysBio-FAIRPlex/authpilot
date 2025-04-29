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

@router.post("/search", response_model=dict)
def run_query(body: SearchQueryRequest, db: Session = Depends(get_db)):
    query = db.query(Person)

    return {
        "columns": COLUMNS,
        "rows": []
    }
