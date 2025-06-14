from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.table import Table, ListTablesResponse

router = APIRouter()

@router.get("/tables", response_model=ListTablesResponse)
async def list_tables(db: Session = Depends(get_db)):
    try:
        tables = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        ).fetchall()

        result = []
        for row in tables:
            table_name = row[0]
            if table_name.startswith("sqlite_"):
                continue

            result.append(Table(
                name=table_name,
                description=f"Table `{table_name}` in the sysbio database.",
                data_model={}
            ))

        return ListTablesResponse(tables=result)
    except Exception as e:
        return ListTablesResponse(tables=[], errors=[{"title": "Internal server error", "detail": str(e)}])
