.PHONY: setup install dev data train sql app all lint format test test-all check clean

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt
	pre-commit install

data:
	python scripts/generate_data.py

train:
	python scripts/train_models.py

sql:
	python scripts/run_sql_analysis.py

app:
	streamlit run app/streamlit_app.py

all: data train sql

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

test:
	pytest -m "not slow"

test-all:
	pytest

check: lint test

clean:
	rm -f data/raw/*.csv data/processed/*.csv data/processed/*.json models/*.joblib analytics/*.duckdb
