# main.py

import urllib.parse
from fastapi import FastAPI, HTTPException, Form
from typing import Annotated, Optional, List
from datetime import datetime, timedelta
import uuid
import os
import httpx
from contextlib import asynccontextmanager
import jwt
from jwcrypto import jwk as jwcryptojwk
import urllib


HYDRA_URL = os.environ.get("HYDRA_URL", "http://hydra")
HYDRA_ADMIN_URL = os.environ.get("HYDRA_ADMIN_URL", "http://hydra-admin:4445")
KRATOS_ADMIN_URL = os.environ.get("KRATOS_ADMIN_URL", "https://kratos-admin:4434")
AMP_PD_VISA_ISSUER_URL = os.environ.get("AMP_PD_VISA_ISSUER_URL",  "http://auth-pilot-amp-pd-visa-issuer.io:7000")
FAIRPLEX_PASSPORT_ISS = os.environ.get("FAIRPLEX_PASSPORT_ISS", "https://sysbio-fairplex.org/")

# Secret key for encoding and decoding JWT (use an environment variable in production)
ALGORITHM = "RS256"
HYDRA_PEM_PRIVATE_KEY: bytes
HYDRA_PEM_PUBLIC_KEY: bytes
HYDRA_KID: str

async def create_hydra_keyset():
    url = f"{HYDRA_ADMIN_URL}/admin/keys/mykeyset" # use this when running outside docker compose network
    headers = {"Content-Type": "application/json"}
    body = {
        "alg": "RS256",
        "kid": "mywebkeyid",
        "use": "sig"
    }
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(url, headers=headers, json=body)
        if response.status_code != 201:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to create key: {response.text}"
            )
        data = response.json()
        # print(json.dumps(data))
        return data

async def get_access_token_keyset():
    url = f"{HYDRA_URL}/.well-known/jwks.json"
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get jwks: {response.status_code} {response.text}"
            )
        data = response.json()
    url = f"{HYDRA_ADMIN_URL}/admin/keys/hydra.jwt.access-token" # use this when running outside docker compose network
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get key: {response.status_code} {response.text}"
            )
        data = response.json()
        return data

async def get_public_key(jwks_uri: str, kid: str):
    headers = {"Accept": "application/json"}

    print(f'Getting public key from {jwks_uri}')
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(jwks_uri, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get JWKS from {jwks_uri}: {response.status_code} {response.text}"
            )
        jwk_data = response.json()
        # print(json.dumps(jwk_data["keys"][0], indent=2))
        for key in jwk_data["keys"]:
            if key["kid"] == kid:
                public_key = jwcryptojwk.JWK(**key).export_to_pem(private_key=False)
                print(f'Got public key: {key["kid"]} from {jwks_uri}')
                return public_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    jwk_data = await get_access_token_keyset()
    jwk_data = jwk_data["keys"][0] # just use first key from Hydra
    # print(json.dumps(jwk_data, indent=2))
    key = jwcryptojwk.JWK(**jwk_data)
    global HYDRA_PEM_PRIVATE_KEY, HYDRA_PEM_PUBLIC_KEY, HYDRA_KID
    # Export Hydra private key. We must sign our tokens with the same keys that Hydra uses so that consumers can verify our token signatures with Hydra!
    HYDRA_PEM_PRIVATE_KEY = key.export_to_pem(private_key=True, password=False) 
    HYDRA_PEM_PUBLIC_KEY = key.export_to_pem(private_key=False)
    HYDRA_KID = jwk_data["kid"]
    # print(HYDRA_PEM_PUBLIC_KEY.decode('utf-8'))
    yield

app = FastAPI(lifespan=lifespan)
        
async def get_identity(id: str):
    url = f"{KRATOS_ADMIN_URL}/admin/identities/{id}"
    print(url)
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(url, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get identity: {response.status_code} {response.text}"
            )
        data = response.json()
        # print(json.dumps(data, indent=2))
        return data

async def get_amp_pd_visas(passport_token: str) -> list[str]:
    # url = f"http://auth-pilot-amp-pd-visa-issuer.io:7000/visas" # use this when running outside docker compose network
    url = f"{AMP_PD_VISA_ISSUER_URL}/visas" # use this when running outside docker compose network
    print(f'Contacting {url}')
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(url, headers=headers, json={"subject_token":passport_token})
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get AMP PD visas: {response.status_code} {response.text}"
            )
        data = response.json()
        # print(json.dumps(data, indent=2))
        return data["visa_tokens"]



def verify_token(token: str, PUBLIC_KEY):
    hdr = jwt.get_unverified_header(token)
    decoded = jwt.decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
    # print(decoded)
    return decoded


@app.post("/token-exchange")
async def token_exchange(
    grant_type: Annotated[str, Form()],
    subject_token: Annotated[str, Form()],
    requested_token_type: Annotated[str, Form()],
    subject_token_type: Annotated[str, Form()],
    resource: List[str] = Form(...)
):
    # Validate the subject_token
    if not subject_token:
        raise HTTPException(
            status_code=400, detail="subject_token is required.")

    # Validate the JWT
    try:
        hdr = jwt.get_unverified_header(subject_token)
        # print(hdr)
        # decoded = jwt.decode(subject_token, options={"verify_signature": False})
        decoded = jwt.decode(subject_token, HYDRA_PEM_PUBLIC_KEY, algorithms=[ALGORITHM])
        print(decoded)

        # now get identity info
        identity_data = await get_identity(decoded["sub"])

        resource_list = resource
        aud_list = set()
        for r in resource_list:
            split_url = urllib.parse.urlsplit(r)
            aud = split_url.scheme+'://'+split_url.netloc
            aud_list.add(aud)

        now = datetime.now()
        headers = {"typ":"urn:ga4gh:params:oauth:token-type:passport",
                   "alg": "RS256",
                   "jku":f"{HYDRA_URL}/.well-known/jwks.json",
                   "kid": HYDRA_KID}
        jti = str(uuid.uuid4())
        passport_payload = {
            "iss": FAIRPLEX_PASSPORT_ISS,
            "sub": identity_data["traits"]["email"],
            "aud": list(aud_list),
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=3600)).timestamp(),
            "jti": jti,
            "ga4gh_passport_v1": []
        }
        # print(passport_payload)
        encoded_passport_jwt = jwt.encode(passport_payload, key=HYDRA_PEM_PRIVATE_KEY, algorithm=ALGORITHM, headers=headers)

        amp_pd_visas = []
        amp_pd_visas = await get_amp_pd_visas(encoded_passport_jwt)
        if len(amp_pd_visas) > 0:
            hdr = jwt.get_unverified_header(amp_pd_visas[0])
            VISA_PUBLIC_KEY = await get_public_key(hdr["jku"], hdr["kid"])
            for visa in amp_pd_visas:
                verify_token(visa, VISA_PUBLIC_KEY)

        passport_payload = {
            "iss": "https://ga4gh.org/",
            "sub": identity_data["traits"]["email"],
            "aud": list(aud_list),
            "iat": now.timestamp(),
            "exp": (now + timedelta(seconds=3600)).timestamp(),
            "jti": jti,
            "ga4gh_passport_v1": amp_pd_visas
        }
        encoded_passport_jwt = jwt.encode(passport_payload, key=HYDRA_PEM_PRIVATE_KEY, algorithm=ALGORITHM, headers=headers)
        print(f"Successfully returning passport jti: {passport_payload['jti']}")
        return {
            "access_token": encoded_passport_jwt,
            "issued_token_type": "urn:ga4gh:params:oauth:token-type:passport",
            "token_type": "Bearer"
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Expired token.")
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401, detail="Invalid token.")
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=500, detail="PyJWT error: " + str(e))    

# Optional: Token generation route for testing purposes
@app.post("/token-generate")
async def token_generate():
    # Example payload (replace with actual user data)
    payload = {"user": "testUser"}
    token = jwt.encode(payload, HYDRA_PEM_PRIVATE_KEY, algorithm=ALGORITHM)
    return {"token": token}
