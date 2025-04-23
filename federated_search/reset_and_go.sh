#!/bin/bash

rm test.db
python init_db.py
fastapi dev main.py
