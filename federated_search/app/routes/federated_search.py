from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import SearchQueryRequest

router = APIRouter()

@router.post("/search", response_model=dict)
def run_query(db: Session = Depends(get_db)):
    return {}
