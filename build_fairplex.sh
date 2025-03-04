#!/bin/bash

set -e

docker compose -f auth-pilot-compose.yaml build
docker compose -f auth-pilot-compose.yaml up --force-recreate