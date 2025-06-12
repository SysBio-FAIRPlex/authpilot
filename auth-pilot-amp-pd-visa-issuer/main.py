from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
import uuid
import httpx
import json
import os
import typing
from urllib.parse import quote
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import jwt
from jwcrypto import jwk as jwcryptojwk
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from google.cloud import storage
import google.auth
from google.auth import compute_engine
from google.auth.transport import requests

# Todo: Get these from environment variables or a secure vault like Google Secret Manager.
# For simplicity, we use fixed values here.
PASSPHRASE = "mySecretPassphrase"
SALT = b"some_fixed_salt"
PRIVATE_KEY: rsa.RSAPrivateKey
PUBLIC_KEY: rsa.RSAPublicKey
PRIVATE_PEM: bytes
PUBLIC_PEM: bytes
PUBLIC_JWK: dict
PRIVATE_PEM_FOR_ENCODE: PrivateKeyTypes

AMP_PD_GROUPS: dict

def generate_visa_keys():
    global PRIVATE_KEY, PUBLIC_KEY, PRIVATE_PEM, PUBLIC_PEM, PASSPHRASE, PRIVATE_PEM_FOR_ENCODE
    # Generate private key
    PRIVATE_KEY = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    # Serialize the private key with passphrase-based encryption. Add some salt.
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(PASSPHRASE.encode()))
    PRIVATE_PEM = PRIVATE_KEY.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(key), # Replace 'your_password'
    )
    # Load the private key using the derived key as password
    PRIVATE_PEM_FOR_ENCODE = serialization.load_pem_private_key(
        PRIVATE_PEM,
        password=key,
        backend=default_backend()
    )
    if PRIVATE_PEM_FOR_ENCODE and not isinstance(PRIVATE_PEM_FOR_ENCODE, rsa.RSAPrivateKey):
        raise ValueError("Failed to load private key from PEM: expecting an RSA private key")

    PUBLIC_KEY = PRIVATE_KEY.public_key()
    PUBLIC_PEM = PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

async def get_amp_pd_groups():
    auth_pilot_terra_groups_url = os.environ.get('AMP_PD_AUTH_URL')
    if not auth_pilot_terra_groups_url:
        raise Exception("AMP_PD_AUTH_URL environment variable is not set")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {'accept': 'application/json'}
            response = await client.get(auth_pilot_terra_groups_url, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses
            global AMP_PD_GROUPS
            AMP_PD_GROUPS = response.json()
            print(AMP_PD_GROUPS)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    generate_visa_keys()
    global PUBLIC_JWK, PUBLIC_PEM
    n,e = PUBLIC_KEY.public_numbers().n, PUBLIC_KEY.public_numbers().e
    # Create a JWK object with the RSA public key parameters
    PUBLIC_JWK = {
        "kty": "RSA",
        "n": base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
        "e": base64.urlsafe_b64encode(e.to_bytes((e.bit_length() + 7) // 8, 'big')).rstrip(b'=').decode('utf-8'),
        "alg": "RS256", # You might need to adjust algorithm depending on use case
        "kid": "VISA_KEY",
        "use": "sig"
    }
    print(json.dumps(PUBLIC_JWK, indent=2))
    print(PUBLIC_PEM.decode("utf-8"))
    # Verify we created the public key correctly
    # public_key = jwcryptojwk.JWK(**PUBLIC_JWK)
    # pem_public_key = public_key.export_to_pem(private_key=False)
    # print(pem_public_key.decode('utf-8'))

    await get_amp_pd_groups()
    yield
    # Cleanup code can be added here if needed

app = FastAPI(lifespan=lifespan)

@app.get("/.well-known/jwks.json")
async def get_jwks():
    global PUBLIC_JWK
    return {
        "keys": [PUBLIC_JWK]
    }

async def get_public_key(jwks_uri: str, kid: str):
    headers = {"Accept": "application/json"}
    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(jwks_uri, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to get JWKS from {jwks_uri}: {response.status_code} {response.text}"
            )
        jwk_data = response.json()
        public_key = None
        for jwk_key in jwk_data["keys"]:
            if jwk_key["kid"] == kid:
                key = jwcryptojwk.JWK(**jwk_key)
                public_key = key.export_to_pem(private_key=False)
                break
        if public_key is None:
            raise HTTPException(
                status_code=404,
                detail=f"Public key with kid {kid} not found in JWKS from {jwks_uri}"
            )
        print(f'Got public key kid:{kid} from {jwks_uri}')
        return public_key

async def verify_token(token: str):
    hdr = jwt.get_unverified_header(token)
    PUBLIC_KEY = await get_public_key(hdr["jku"], hdr["kid"])
    decoded = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"], options={"verify_aud":False})
    return decoded

# Define the request body model
class VisaRequest(BaseModel):
    subject_token: str

@app.post("/visas")
async def get_visas(request: VisaRequest):
    global PRIVATE_PEM_FOR_ENCODE, AMP_PD_GROUPS
    try:

        # Decode the JWT token to get the email
        hdr = jwt.get_unverified_header(request.subject_token)
        decoded = jwt.decode(request.subject_token, algorithms=["RS256"], options={"verify_signature": False})
        print(decoded)
        email = decoded["sub"]
        now = datetime.now(timezone.utc)
        iat = now.timestamp()
        exp = (now + timedelta(seconds=3600)).timestamp()

        if email in AMP_PD_GROUPS['adminsEmails'] or email in AMP_PD_GROUPS['membersEmails']: # field names from Terra API response
            # User is in the approved group. Create Visas for AMP PD 
            # Each is signed separately
            now = datetime.now()
            hostname = os.environ.get('HOSTNAME', 'auth-pilot-amp-pd-visa-issuer.io')
            headers={
                "typ": "vnd.ga4gh.visa+jwt", # Visa Document Token Format https://ga4gh.github.io/data-security/aai-openid-connect-profile#visa-document-token-format
                "alg": "RS256", "kid": "VISA_KEY",
                # "jku": "http://host.docker.internal:7000/.well-known/jwks.json",
                "jku": f"{hostname}/.well-known/jwks.json", 
                "kid": PUBLIC_JWK["kid"]
            }
            tier1_visa_payload = {
                "iss": "http://amp-pd.org/",
                "sub": email,
                "iat": iat,
                "exp": exp,
                "jti": str(uuid.uuid4()),
                "ga4gh_visa_v1": {
                    "type": "ControlledAccessGrants",
                    "asserted": iat,
                    "value": "https://www.amp-pd.org/tier1",
                    "source": "https://www.amp-pd.org",
                    "by": "dac"
                }
            }
            # Create the Visa tokens
            # Use typing.cast to tell type checker that PRIVATE_PEM_FOR_ENCODE is a RSAPrivateKey
            tier1_visa = jwt.encode(tier1_visa_payload, typing.cast(rsa.RSAPrivateKey, PRIVATE_PEM_FOR_ENCODE), algorithm="RS256", headers=headers)
            tier2_visa_payload = {
                    "iss": "http://amp-pd.org/",
                    "sub": email,
                    "iat": iat,
                    "exp": exp,
                    "jti": str(uuid.uuid4()),
                    "ga4gh_visa_v1": {
                        "type": "ControlledAccessGrants",
                        "asserted": iat,
                        "value": "https://www.amp-pd.org/tier2",
                        "source": "https://www.amp-pd.org",
                        "by": "dac"
                    }
                }
            tier2_visa = jwt.encode(tier2_visa_payload, typing.cast(rsa.RSAPrivateKey, PRIVATE_PEM_FOR_ENCODE), algorithm="RS256", headers=headers)
            return {"visa_tokens": [tier1_visa, tier2_visa]}

        else:
            return {"visa_tokens":[]}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


######################################################
# Mock a DRS server. Generate signed URL on demand.
######################################################

# command to create signed url:
# gcloud storage sign-url gs://auth-pilot-test-data/test-data.txt --private-key-file=./auth-spike-445014-d6cebb32a765.json --duration=120m

def generate_download_signed_url_v4(bucket_name, blob_name):
    """Generates a v4 signed URL for downloading a blob.

    This method uses the Service Account for this Cloud Run service.
    The Service Account needs the roles/iam.serviceAccountTokenCreator role.
    """
    credentials, _ = google.auth.default()
    
    auth_request = requests.Request()
    credentials.refresh(auth_request)
    
    signing_credentials = compute_engine.IDTokenCredentials(
      auth_request,
      "",
      service_account_email=os.environ.get("SERVICE_ACCOUNT")
    )

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        # This URL is valid for 15 minutes
        expiration=timedelta(minutes=15),
        # Allow GET requests using this URL.
        method="GET",
        credentials=signing_credentials
    )

    print("Generated GET signed URL:")
    print(url)
    print("You can use this URL with any user agent, for example:")
    print(f"curl '{url}'")
    return url


class DRS_Request(BaseModel):
    passports: list[str]

# Provide a DRS stub for testing
@app.post("/drs/v1/objects/{rest_of_path:path}")
async def drs_get_data(rest_of_path: str, request: Request, drs_req: DRS_Request | None):
    # # Verify passports and visas
    # for passport in drs_req.passports:
    #     decoded = await verify_token(passport)
    #     for visa in decoded["ga4gh_passport_v1"]:
    #         decoded = await verify_token(visa)

    # return {"signed_url":os.environ.get("SIGNED_URL")}

    bucket_blob = os.path.split(rest_of_path)
    print(bucket_blob)
    return {"signed_url": generate_download_signed_url_v4(bucket_blob[0], bucket_blob[1])}

# To run the app, use: uvicorn main:app --host 0.0.0.0 --port 8080
