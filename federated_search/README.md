# FAIRplex Federated Search Service

Goal: Create a unified API that enables client tools (like FAIRkit) to query data across AMP programs with respect to federation and governance.

[SysBio: GA4GH Auth, Search API, & File Discovery doc](https://docs.google.com/document/d/1Im4XDBghVmgdPPercQi4Vg1aODB6kbfam1h10zqTHIM/edit?tab=t.0#heading=h.d5wb9roh9o17)

## Setup
1. Create a python virtual environment for dependencies.
```sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
2. Create the databases with `./init_dbs.sh`

## Run app
1. Ensure you have run the setup section above.
2. Run `docker compose up --build --force-recreate -d`
3. Visit `localhost:8000/docs` for the swagger UI
4. If at any time you want to reset the database, stop the containers with `docker compose down`, re-run `./init_dbs.sh` script and rerun `docker compose up --build --force-recreate -d`

## Run tests
1. Ensure you have run the setup section above.
2. Run `pytest tests`

## Deploy
The services are deployed as Cloud Run on GCP.

### Enable APIs
Enable the following APIs:
  - Cloud Build
  - Cloud Run
  - Secret Manager

Grant the Default Compute Service Account the following roles:
  - Storage Admin
  - Log Writer
  - Artifact Registry Administrator
  - Secret Manager Secret Accessor

### Create Artifact Repos

### Environment variables
Set the following variables in .env files:

### Deploy script
Run the `deploy.sh` script to deploy to Google Cloud Run. The script takes parameters for which services to deploy.
For example, to deploy all services, run the command

```sh
./deploy.sh all
```