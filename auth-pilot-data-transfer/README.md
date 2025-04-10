# FAIRplex Auth Pilot Data Transfer Service

## Deployment Notes
You must set up the Cloud Run service to use a Service Account with the correct roles to access Cloud Storage.

## Build Docker image
```
docker build -t auth-pilot-data-transfer:0.1 .
docker tag auth-pilot-data-transfer:0.1 us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-data-transfer:0.1 && \
docker push us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-data-transfer:0.1
```