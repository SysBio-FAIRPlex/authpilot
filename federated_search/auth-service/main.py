import os
import httpx
from db import OAuthState, IssuedToken, get_db
from fastapi import FastAPI, Request, Query, HTTPException, Form, Depends, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from authlib.integrations.starlette_client import OAuth
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
from urllib.parse import urlencode
import uuid

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY"))
if JWT_SECRET is None:
    raise ValueError("JWT_SECRET or SECRET_KEY must be set in the environment.")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()
SECRET_KEY = os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise ValueError("SECRET_KEY must be set in the environment")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "https://sysbio-344651184654.us-central1.run.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = Config('.env')
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=config('GOOGLE_CLIENT_ID'),
    client_secret=config('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

def get_current_user(token: str = Depends(oauth2_scheme)):
    assert JWT_SECRET is not None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload

@app.get("/")
def home(request: Request):
    user = request.session.get('user')
    if user:
        return HTMLResponse(f"<h1>Hello {user['name']}</h1><a href='/logout'>Logout</a>")
    return HTMLResponse("<a href='/login'>Login with Google</a>")


@app.get("/login")
def login(
    redirect_uri: str = Query(description="Client redirect URI"),
    state: str = Query(),
    db: Session = Depends(get_db)
):
    existing = db.query(OAuthState).filter_by(state=state).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"State {state} already exists - use a different state.")

    db.add(OAuthState(state=state, redirect_uri=redirect_uri))
    db.commit()

    params = {
        "response_type": "code",
        "client_id": config("GOOGLE_CLIENT_ID"),
        "redirect_uri": config("REDIRECT_URI"),
        "scope": "openid email profile",
        "prompt": "consent",
        "state": state
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url)

@app.get("/callback")
async def callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    state_entry = db.query(OAuthState).filter_by(state=state).first()
    if not state_entry:
        raise HTTPException(400, "Invalid or expired state")
    redirect_uri = state_entry.redirect_uri
    db.delete(state_entry)
    db.commit()
    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": config('GOOGLE_CLIENT_ID'),
                "client_secret": config('GOOGLE_CLIENT_SECRET'),
                "redirect_uri": config('REDIRECT_URI'),
                "grant_type": "authorization_code"
            }
        )
        tokens = token_res.json()
        userinfo_res = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
    user = userinfo_res.json()
    expire_time = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user["sub"],
        "email": user["email"],
        "name": user.get("name"),
        "exp": expire_time,
    }
    assert JWT_SECRET is not None
    access_token = jwt.encode(to_encode, JWT_SECRET, ALGORITHM)
    db.add(IssuedToken(
        state=state,
        access_token=access_token,
        user_sub=user["sub"],
        user_email=user["email"],
        issued_at=datetime.utcnow(),
        expires_at=expire_time
    ))
    db.commit()
    params = {
        "state": state,
        "code": code
    }
    redirect_uri = f"{redirect_uri}?{urlencode(params)}"
    return RedirectResponse(f"{redirect_uri}")

@app.get("/passport")
def show_passport(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/login")
    return {"message": "Authenticated user", "user": user}

@app.get("/session")
def session_info(state: str, db: Session = Depends(get_db)):
    token = db.query(IssuedToken).filter_by(state=state).first()
    if token:
        user = {
            "email": token.user_email,
            "sub": token.user_sub 
        }
        return {
            "access_token": token.access_token,
            "token_type": "bearer",
            "user": user,
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")

class TokenRequest(BaseModel):
    code: str
    redirect_uri: str
    client_id: str
    grant_type: str

@app.post("/token")
async def exchange_token(
    code: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    grant_type: str = Form(...),
    code_verifier: str = Form(None)  # optional
):
    if grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Unsupported grant_type")

    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": config("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": redirect_uri,
        "grant_type": grant_type,
    }

    if code_verifier:
        payload["code_verifier"] = code_verifier

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://oauth2.googleapis.com/token", data=payload)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


def load_private_key():
    with open(config('PRIVATE_KEY_PATH'), "r") as f:
        return f.read()


@app.get("/userinfo")
def userinfo(request: Request, user=Depends(get_current_user)):
    now = int(datetime.utcnow().timestamp())
    exp = now + 12 * 3600

    # Create a dummy visa (normally you’d do this per DAC access or external system)
    visa_claim = {
        "iss": config('ISSUER'),
        "sub": user["sub"],
        "iat": now,
        "exp": exp,
        "jti": str(uuid.uuid4()),
        "ga4gh_visa_v1": {
            "type": "ControlledAccessGrants",
            "asserted": now,
            "value": "phs000123.v1.p1.c1",
            "source": config('ISSUER'),
            "by": "dac"
        }
    }

    visa_jwt = jwt.encode(visa_claim, load_private_key(), algorithm="RS256")

    return {
        "sub": user["sub"],
        "name": user["name"],
        "email": user["email"],
        "iss": config('ISSUER'),
        "iat": now,
        "exp": exp,
        "scope": "openid ga4gh_passport_v1",
        "ga4gh_passport_v1": [visa_jwt]
    }