#!/bin/bash

set -o errexit

PROJECT_ID="sysbio-fed-search-dev"
gcloud config set project "${PROJECT_ID}"

deploy_pd() {
  echo "Deploying PD service..."
  gcloud builds submit ./amp-pd-service \
    --tag "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-pd"

  gcloud run deploy amp-pd \
    --image "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-pd" \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=sqlite:///./pd.db"
}

deploy_ad() {
  echo "Deploying AD service..."
  gcloud builds submit ./amp-ad-service \
    --tag "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-ad"

  gcloud run deploy amp-ad \
    --image "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/amp-ad" \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "DATABASE_URL=sqlite:///./ad.db"
}

deploy_sysbio() {
  echo "Deploying SysBio service..."
  gcloud builds submit ./sysbio-service \
    --tag "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/sysbio"

  gcloud run deploy sysbio \
    --image "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/sysbio" \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "AMP_PD_URL=https://amp-pd-344651184654.us-central1.run.app,AMP_AD_URL=https://amp-ad-344651184654.us-central1.run.app,DATABASE_URL=sqlite:///./sysbio.db"
}

deploy_auth() {
  echo "Deploying Auth service..."
  gcloud builds submit ./auth-service \
    --tag "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/auth"

  gcloud run deploy auth \
    --image "us-central1-docker.pkg.dev/${PROJECT_ID}/docker-repo/auth" \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars "REDIRECT_URI=https://auth-344651184654.us-central1.run.app/callback"
}

if [[ $# -eq 0 ]]; then
  echo "Usage: ./deploy.sh [pd] [ad] [sysbio] [auth] [all]"
  exit 1
fi

for service in "$@"; do
  case "$service" in
    pd) deploy_pd ;;
    ad) deploy_ad ;;
    sysbio) deploy_sysbio ;;
    auth) deploy_auth ;;
    all)
      deploy_pd
      deploy_ad
      deploy_sysbio
      deploy_auth
      ;;
    *)
      echo "Unknown service: $service"
      exit 1
      ;;
  esac
done
