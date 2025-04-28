from app.database import Base, engine, SessionLocal
from app.models import Person
from google.cloud import bigquery

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

    print("Querying BQ for initial data...")
    sync_bigquery_to_sqlite()
    print("BigQuery data loaded into SQLite.")

def sync_bigquery_to_sqlite():
    # TODO
    pass

if __name__ == "__main__":
    init_db()
