#!/bin/bash

set -o errexit

PROJECT_ID="sysbio-fed-search-dev"

gcloud config set project "${PROJECT_ID}"

# PD

gcloud builds submit ./amp-pd-service \
  --tag "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-pd"

gcloud run deploy amp-pd \
  --image "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-pd" \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=sqlite:///./pd.db"

# AD

gcloud builds submit ./amp-ad-service \
  --tag "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-ad"

gcloud run deploy amp-ad \
  --image "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-ad" \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=sqlite:///./ad.db"

# sysbio

gcloud builds submit ./sysbio-service \
  --tag "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/sysbio"

gcloud run deploy sysbio \
  --image "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/sysbio" \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "AMP_PD_URL=https://amp-pd-344651184654.us-central1.run.app,AMP_AD_URL=https://amp-ad-344651184654.us-central1.run.app,DATABASE_URL=sqlite:///./sysbio.db"
