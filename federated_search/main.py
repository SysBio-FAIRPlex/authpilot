from fastapi import FastAPI
from app.routes import federated_search

app = FastAPI()
app.include_router(federated_search.router)
