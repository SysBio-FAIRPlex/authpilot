# FAIRplex Federated Search Service

Goal: Create a unified API that enables client tools (like FAIRkit) to query data across AMP programs with respect to federation and governance.

[SysBio: GA4GH Auth, Search API, & File Discovery doc](https://docs.google.com/document/d/1Im4XDBghVmgdPPercQi4Vg1aODB6kbfam1h10zqTHIM/edit?tab=t.0#heading=h.d5wb9roh9o17)

## Setup
1. Create a python virtual environment for dependencies.
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
2. Create the database with `python init_db.py`

## Run app
1. Ensure you have run the setup section above.
2. Run `fastapi dev main.py`
3. Visit `localhost:8000/docs` for the swagger UI
4. If at any time you want to reset the database, there is a `reset_and_go.sh` script that will wipe the database and start the app.

## Run tests
1. Ensure you have run the setup section above.
2. Run `pytest tests`
