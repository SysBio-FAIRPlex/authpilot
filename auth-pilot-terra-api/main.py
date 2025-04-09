from fastapi import FastAPI, HTTPException, Depends
import httpx
import os
from urllib.parse import quote

app = FastAPI()

@app.get("/api/group/{group_name}")
async def get_groups(group_name: str):
    # Get the authorization token from the Google metadata server
    try:
        async with httpx.AsyncClient() as client:
            metadata_url = f"http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=https://api.firecloud.org"
            headers = {"Metadata-Flavor": "Google"}
            token_response = await client.get(metadata_url, headers=headers)
            token_response.raise_for_status()  # Raise an error for bad responses
            token = token_response.text
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Send a GET request to the Firecloud API
    try:
        api_url = f"{os.environ.get('FIRECLOUD_API_URL')}/{quote(group_name)}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            api_response = await client.get(api_url, headers=headers)
            api_response.raise_for_status()  # Raise an error for bad responses
            return api_response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

# To run the app, use: uvicorn main:app --host 0.0.0.0 --port 8080
