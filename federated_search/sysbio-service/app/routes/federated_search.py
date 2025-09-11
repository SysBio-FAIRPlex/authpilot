import re
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.error import ErrorResponse
from app.utils.error_utils import error_response
from app.dependencies import get_db
from app.schemas import SearchRequest
from jose import jwt, JWTError
from typing import Dict, Any, Optional
import httpx
import os

router = APIRouter()
JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY"))
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

AMP_PD_URL = os.getenv("AMP_PD_URL")
AMP_AD_URL = os.getenv("AMP_AD_URL")

def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    if token is None:
        return None
    assert JWT_SECRET is not None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload

@router.post(
    "/search",
    response_model=dict,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request due to invalid input"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def run_query(request: SearchRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Prepare parameter dict
    if isinstance(request.parameters, dict):
        params: Dict[str, Any] = request.parameters.copy()
    elif request.parameters is None:
        params = {}
    else:
        raise HTTPException(
            status_code=400,
            detail="Only named parameters (dict[str, Any]) are supported for pagination"
        )

    query_base = request.query.strip().rstrip(';')
    pagination_supported = not re.search(r'\blimit\b', query_base, flags=re.IGNORECASE)

    if pagination_supported:
        query_base += " LIMIT :limit OFFSET :offset"
        params["limit"] = request.limit or 10
        params["offset"] = request.offset or 0

    try:
        stmt = text(query_base)
        result = db.execute(stmt, params)
        rows = result.fetchall()
        public_data = [
            {**dict(row._mapping), "source": "public"}
            for row in rows
        ]
    except Exception as e:
        return error_response(400, title="Invalid SQL", detail=f"Invalid SQL: {e}")

    public_restricted = {}
    if not user:
        public_restricted = {
            "year_of_birth": "Visible to logged-in users",
            "race": "Visible to logged-in users"
        }
        for row in public_data:
            for field in public_restricted:
                row.pop(field, None)

    pd_data, ad_data = [], []
    pd_restricted = {}
    sources = {"public": len(public_data)}

    if user:
        async with httpx.AsyncClient() as client:
            try:
                pd_response = await client.post(f"{AMP_PD_URL}/search", json=request.model_dump())
                if pd_response.status_code == 200:
                    pd_json = pd_response.json()
                    pd_data = pd_json.get("data", [])
                    pd_restricted = pd_json.get("restricted_fields", {})

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

    restricted_fields = {}
    if pd_restricted:
        for field, reason in pd_restricted.items():
            restricted_fields.setdefault(field, []).append({"source": "pd", "reason": reason})
    if public_restricted:
        for field, reason in public_restricted.items():
            restricted_fields.setdefault(field, []).append({"source": "public", "reason": reason})


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

    # Build next_page_url only if pagination was applied
    next_page_url = None
    if pagination_supported and len(all_data) == (request.limit or 10):
        offset = request.offset or 0
        limit = request.limit or 10
        next_offset = offset + limit
        next_page_url = f"/search?offset={next_offset}&limit={limit}"

    return {
        "data_model": data_model,
        "data": all_data,
        "sources": sources,
        "restricted_fields": restricted_fields,
        "pagination": {
            "next_page_url": next_page_url
        }
    }

@router.get(
    "/ga4gh/drs/v1/objects/{object_id}",
    response_model=dict,
    responses={
        200: {"description": "DRS object returned successfully"},
        404: {"description": "Object not found"},
    }
)
async def get_drs_object(
    object_id: str = Path(..., description="Unique identifier for the DRS object"),
    user=Depends(get_current_user)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    DRS_OBJECTS = {
        "xyz001": "ad_sample1.bam",
        "xyz002": "ad_sample2.bam",
        "xyz003": "ad_sample3.bam",
        "xyz004": "ad_sample4.bam",
        "xyz005": "ad_sample5.bam",
        "xyz006": "ad_sample6.bam",
        "xyz007": "ad_sample7.bam",
        "xyz008": "ad_sample8.bam",
        "xyz009": "ad_sample9.bam",
        "xyz010": "ad_sample10.bam",
        "abc123": "sample1.bam",
        "def456": "sample2.bam",
        "ghi789": "sample3.bam",
        "jkl012": "sample4.bam",
        "mno345": "sample5.bam",
        "pqr678": "sample6.bam",
        "stu901": "sample7.bam",
        "vwx234": "sample8.bam",
        "yz5678": "sample9.bam",
        "abc999": "sample10.bam",
    }

    drs_object = {
        "id": object_id,
        "self_uri": f"drs://fairkit.example.org/{object_id}",
        "description": "Example DRS object",
        "created_time": "2023-10-10T12:00:00Z",
        "updated_time": "2023-10-11T12:00:00Z",
        "version": "1",
        "mime_type": "application/json",
        "checksums": [
            {"checksum": "1a79a4d60de6718e8e5b326e338ae533", "type": "md5"}
        ],
        "size": 1024,
        "aliases": ["test-object"],
        "access_methods": [
            {
                "type": "https",
                "access_url": {
                    "url": f"https://storage.googleapis.com/willyn-public/{DRS_OBJECTS[object_id]}"
                },
                "region": "us-central1"
            }
        ]
    }

    return JSONResponse(content=drs_object)
