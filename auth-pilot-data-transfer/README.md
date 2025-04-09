# FAIRplex Auth Pilot Data Transfer Service

# Deployment Notes
You must authorize this service to use your personal ADC for project Auth-Spike in SysBio. In the cloud, we must set up to use a service account with the correct roles to access Cloud Storage.
```
gcloud auth application-default login
```

Build Docker image
```
docker build -t auth-pilot-data-transfer:0.1 .
docker tag auth-pilot-data-transfer:0.1 us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-data-transfer:0.1 && \
docker push us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-data-transfer:0.1
```