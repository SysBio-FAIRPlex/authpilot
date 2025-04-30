#!/bin/bash

set -o errexit
set -o nounset

cd amp-pd-service
echo "Wiping local db..."
rm -rf *.db
echo "Local db wiped."
DATABASE_URL="sqlite:///./pd.db" python init_db.py

cd ../amp-ad-service
echo "Wiping local db..."
rm -rf *.db
echo "Local db wiped."
DATABASE_URL="sqlite:///./ad.db" python init_db.py

cd ../sysbio-service
echo "Wiping local db..."
rm -rf *.db
echo "Local db wiped."
DATABASE_URL="sqlite:///./sysbio.db" python init_db.py
