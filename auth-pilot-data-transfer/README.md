# FAIRplex Auth Pilot Data Transfer Service

# Deployment Notes
You must authorize this service to use your personal ADC for project Auth-Spike in SysBio. In the cloud, we must set up to use a service account with the correct roles to access Cloud Storage.
```
gcloud auth application-default login
```

Build Docker image
```
docker build -t auth-pilot-data-transfer:0.1 .
```