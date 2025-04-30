from fastapi import FastAPI
from app.routes import search

app = FastAPI()

app.include_router(search.router)
