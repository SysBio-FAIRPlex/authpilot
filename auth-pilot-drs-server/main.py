# To run: `uvicorn main:app --reload`
# Then go to http://localhost:8000/docs

from fastapi import FastAPI, HTTPException
import jwt
from pydantic import BaseModel
from typing import List
from google.cloud import storage
import uuid

app = FastAPI()
storage_client = storage.Client()
# spds stands for syntehtic proteomics dataset
BUCKET_NAME = "amp-pd-community-workspace-spds"

# In-memory mapping of UUIDs to GCS blob names
drs_id_to_blob = {}

class DRSAccessURL(BaseModel):
    url: str

def get_or_create_drs_id(blob_name: str) -> str:
    # Generate a new UUID if not already mapped
    for drs_id, name in drs_id_to_blob.items():
        if name == blob_name:
            return drs_id
    new_drs_id = str(uuid.uuid4())
    drs_id_to_blob[new_drs_id] = blob_name
    return new_drs_id

@app.get("/objects/{object_id}")
def get_object(object_id: str):
    blob_name = drs_id_to_blob.get(object_id)
    if not blob_name:
        raise HTTPException(status_code=404, detail="Object ID not found")

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    if blob.exists():
        return {
            "id": object_id,
            "name": blob.name,
            "size": blob.size,
            "urls": [DRSAccessURL(url=f"storage.cloud.google.com/{BUCKET_NAME}/{blob.name}")]
        }
    else:
        raise HTTPException(status_code=404, detail="Object not found")

@app.get("/access/{object_id}")
def get_access_url(object_id: str):
    blob_name = drs_id_to_blob.get(object_id)
    if not blob_name:
        raise HTTPException(status_code=404, detail="Object ID not found")

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    if blob.exists():
        #return [DRSAccessURL(url=f"https://storage.googleapis.com/{BUCKET_NAME}/{blob.name}")]
        return [DRSAccessURL(url=f"https://storage.cloud.google.com/{BUCKET_NAME}/{blob.name}")]
    else:
        raise HTTPException(status_code=404, detail="Object not found")

@app.post("/register")
def register_object(blob_name: str):
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Blob not found in bucket")
    drs_id = get_or_create_drs_id(blob_name)
    return {"drs_id": drs_id}

class TransferRequest(BaseModel):
    dst_bucket: str
    list_of_files: List[str]

@app.post("/transfer")
def transfer(request: TransferRequest):
    for filename in request.list_of_files:
        source_bucket_name = "willyn-dsub-test"
        source_bucket = storage_client.bucket(source_bucket_name)
        source_blob = source_bucket.blob(filename)

        destination_bucket = storage_client.bucket(request.dst_bucket)

        source_bucket.copy_blob(source_blob, destination_bucket, filename)
    return {'message': 'ok'}

# Define the request body model
class ListOfFilesRequest(BaseModel):
    passport_token: str

@app.post("/list_of_files")
def list_of_files(request: ListOfFilesRequest):
    decoded_token = jwt.decode(request.passport_token, options={"verify_signature": False})

    sub = decoded_token['sub']
    if "willyn" in sub:
        pass
    else:
        raise HTTPException(status_code=403, detail=f"Unauthorized user {sub}")

    visa_token = decoded_token["ga4gh_passport_v1"][1] # Grabbing the second one for tier 2
    decoded_visa_token = jwt.decode(visa_token, options={"verify_signature": False})
    visa_value = decoded_visa_token["ga4gh_visa_v1"]["value"]
    print(f"In list of files, got the visa, its value is {visa_value}")
    list_of_pd_filenames = [
        "Simulated_Cardio_CSF_NPX",
        "Simulated_Demographics",
        "Simulated_Neu_CSF_NPX",
        "Simulated_amp_pd_participant_apoe_mutations",
        "Simulated_amp_pd_participant_mutations_updated"
    ]
    list_of_ad_filenames = [
        "CHDWB_Clinical.csv",
        "CognitiveClinical_VariablesCode.csv",
        "GG_to_chdwb_for_PHS_gene_data.csv"
    ]
    return {
        "pd_files": list_of_pd_filenames,
        "ad_files": list_of_ad_filenames
    }

    # syn9778337 CHDWB_Clinical.csv
    # syn9778338 CHDWB_CognitiveAssessments