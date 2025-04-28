#!/bin/bash

set -o errexit
set -o nounset

echo "Wiping local db..."
rm -f test.db
echo "Local db wiped."
python init_db.py
fastapi dev main.py --port 8001
