from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models import Person
from app.schemas import SearchRequest

router = APIRouter()

DATA_MODEL = {
    "type": "object",
    "properties": {
        "person_id": {"type": "integer"},
        "gender": {"type": "string"},
        "year_of_birth": {"type": "integer"},
        "race": {"type": "string"},
        "ethnicity": {"type": "string"},
        "diagnosis_name": {"type": "string"}
    },
    "required": ["person_id", "gender", "year_of_birth", "race", "ethnicity", "diagnosis_name"]
}

ROW_LIMIT = 10

@router.post("/search", response_model=dict)
def run_query(request: SearchRequest, db: Session = Depends(get_db)):
    query = db.query(Person).limit(ROW_LIMIT)
    results = [r.to_row() for r in query.all()]

    return {
        "data_model": DATA_MODEL,
        "data": results,
        "pagination": {"next_page_url": None}
    }
