# FAIRplex Auth Pilot AMP PD Visa Issuer Service

A service to demonstrate generating GA4GH Visas for AMP PD.

## Application Initialization
We generate a new RSA private/public key pair at startup each time. We get the list of all emails in AMP PD Terra group "authpilot" (the group name is specified as an env variable) by querying the auth-pilot-terra-api service.


## Docker
Commands to build/tag Docker image and push to repository. **Change for your specific versions and repository. Create repository in Google Cloud Artifact Registry.**

```
docker build -t auth-pilot-amp-pd-visa-issuer:0.1 .
docker tag auth-pilot-amp-pd-visa-issuer:0.1 us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-amp-pd-visa-issuer:0.1 && \
docker push us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/auth-pilot-amp-pd-visa-issuer:0.1
```