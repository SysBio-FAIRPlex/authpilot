```
docker build -f Dockerfile -t fairplex-client-app:0.1 .
docker tag fairplex-client-app:0.1 us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/fairplex-client-app:0.1
docker push us-central1-docker.pkg.dev/auth-spike-445014/auth-pilot/fairplex-client-app:0.1
```