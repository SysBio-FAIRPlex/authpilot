from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from google.cloud import storage
import os
from urllib.parse import urlparse
import tempfile

app = FastAPI()

# Pydantic model for request body
class DownloadRequest(BaseModel):
    signed_url: str
    destination_bucket: str
    destination_path: str


# Initialize Google Cloud Storage client
storage_client = storage.Client()

@app.post("/transfer")
async def download_and_upload(request: DownloadRequest):
    try:
        # Get the bucket
        bucket = storage_client.bucket(request.destination_bucket)
        
        # Extract filename from URL
        parsed_url = urlparse(request.signed_url)
        filename = request.destination_path+'/'+os.path.basename(parsed_url.path)
        
        if not filename:
            filename = "downloaded_file"
        
        # Generate a URL for the uploaded file
        gcs_url = f"gs://{request.destination_bucket}/{filename}"

        print(f"Transferring to {gcs_url}")
        
        # Download file from signed URL
        response = requests.get(request.signed_url, stream=True)
        response.raise_for_status()  # Raise exception for unsuccessful status codes
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write the downloaded content to temporary file
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            
            temp_file_path = temp_file.name
        
        try:
            # Upload the file to Google Cloud Storage
            blob = bucket.blob(filename)
            blob.upload_from_filename(temp_file_path)
            
            
            # Clean up the temporary file
            os.unlink(temp_file_path)
            print(f"Done transferring {gcs_url}")
            return {
                "message": f"File transfer successful",
                "gcs_url": gcs_url
            }
            
        except Exception as e:
            # Clean up the temporary file in case of error
            os.unlink(temp_file_path)
            raise HTTPException(status_code=500, detail=f"Error uploading to GCS: {str(e)}")
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Error downloading file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

