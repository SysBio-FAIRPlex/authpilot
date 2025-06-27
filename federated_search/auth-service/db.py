from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = "sqlite:///./state.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class OAuthState(Base):
    __tablename__ = "oauth_state"

    state = Column(String, primary_key=True, index=True)
    redirect_uri = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class IssuedToken(Base):
    __tablename__ = "issued_token"

    state = Column(String, primary_key=True, index=True)
    access_token = Column(String, index=True)
    user_sub = Column(String, index=True)
    user_email = Column(String)
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

Base.metadata.create_all(bind=engine)
