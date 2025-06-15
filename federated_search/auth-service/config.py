from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env into os.environ

GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:8000/callback")
ISSUER = os.environ.get("ISSUER", "http://localhost:8000")

PRIVATE_KEY_PATH = "private_key.pem"
PUBLIC_KEY_PATH = "public_key.pem"
