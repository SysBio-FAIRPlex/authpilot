from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import SearchQueryRequest

router = APIRouter()

COLUMNS = ["ID", "Sex At Birth", "Age At Baseline", "Latest Diagnosis"]

AMP_PD_EXAMPLE_DATA = [
    [12345, "Female", 80, "Parkinson's Disease"],
    [23456, "Female", 81, "Parkinson's Disease"],
]
AMP_AD_EXAMPLE_DATA = [
    [34567, "Female", 82, "Alzheimer's Disease"],
    [45678, "Female", 83, "Alzheimer's Disease"],
]
PUBLIC_DATA = [
    [11111, "Female", 70, "No Disease Nor Other Disorder"]
]

@router.post("/search", response_model=dict)
def run_query(body: SearchQueryRequest, db: Session = Depends(get_db)):
    if body.pd_access and body.ad_access:
        return {
            "columns": COLUMNS,
            "rows": AMP_PD_EXAMPLE_DATA + AMP_AD_EXAMPLE_DATA + PUBLIC_DATA
        }
    elif body.pd_access:
        return {
            "columns": COLUMNS,
            "rows": AMP_PD_EXAMPLE_DATA + PUBLIC_DATA
        }
    elif body.ad_access:
        return {
            "columns": COLUMNS,
            "rows": AMP_AD_EXAMPLE_DATA + PUBLIC_DATA
        }
    else:
        return {
            "columns": COLUMNS,
            "rows": PUBLIC_DATA
        }
