.PHONY: setup data train sql app all clean

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

data:
	python scripts/generate_data.py

train:
	python scripts/train_models.py

sql:
	python scripts/run_sql_analysis.py

app:
	streamlit run app/streamlit_app.py

all: data train sql

clean:
	rm -f data/raw/*.csv data/processed/*.csv data/processed/*.json models/*.joblib analytics/*.duckdb
