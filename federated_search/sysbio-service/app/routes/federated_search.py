from app.models.error import ErrorResponse
from app.utils.error_utils import error_response
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.dependencies import get_db
from app.schemas import SearchRequest
from dotenv import load_dotenv
import httpx
import os

load_dotenv()
AMP_PD_URL = os.getenv("AMP_PD_URL")
AMP_AD_URL = os.getenv("AMP_AD_URL")

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY"))
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# I'm arbitrarily choosing people with ID <= 1500 to be in PD,
# people with 1500 < ID <= 3000 to be in AD,
# and everyone above 3000 to be public
MAX_PD_ID = 1500
MAX_AD_ID = 3000

ROW_LIMIT = 10

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload  # or map to a user model if needed

@router.post(
    "/search",
    response_model=dict,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request due to invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def run_query(request: SearchRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ad_access = request.parameters.get("ad_access", False) if isinstance(request.parameters, dict) else False

    try:
        stmt = text(request.query)
        result = db.execute(stmt, request.parameters or [])
        rows = result.fetchall()
        public_data = [dict(row._mapping) for row in rows]
    except Exception as e:
        return error_response(400, title="Invalid SQL", detail=f"Invalid SQL: {e}")

    pd_data, ad_data = [], []
    sources = {"public": len(public_data)}

    async with httpx.AsyncClient() as client:
        try:
            pd_response = await client.post(f"{AMP_PD_URL}/search", json=request.model_dump())
            if pd_response.status_code == 200:
                pd_data = pd_response.json()["data"]
                sources["pd"] = len(pd_data)
            elif pd_response.status_code == 403:
                sources["pd"] = 403
            else:
                pd_response.raise_for_status()
        except Exception as e:
            print(f"PD service error: {e}")
            sources["pd"] = 0

        try:
            ad_response = await client.post(f"{AMP_AD_URL}/search", json=request.model_dump())
            if ad_response.status_code == 200:
                ad_data = ad_response.json()["data"]
                sources["ad"] = len(ad_data)
            elif ad_response.status_code == 403:
                sources["ad"] = 403
            else:
                ad_response.raise_for_status()
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
