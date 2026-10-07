PY ?= python
export PYTHONHASHSEED=0

.PHONY: setup lint format test test-all reproduce notebook report app checkpoint clean

setup:
	$(PY) -m pip install -r requirements-dev.txt
	pre-commit install

lint:
	ruff check .
	ruff format --check .

format:
	ruff format . && ruff check --fix .

test:
	pytest

test-all:
	pytest -m "" --cov --cov-report=term-missing

reproduce:
	$(PY) scripts/run_benchmark.py
	$(PY) scripts/run_noisy.py
	$(PY) scripts/make_figures.py

notebook:
	jupyter nbconvert --to notebook --execute --inplace notebooks/qfolio.ipynb

report:
	bash scripts/build_report.sh

app:
	streamlit run app/streamlit_app.py

checkpoint:
	$(PY) -m qportfolio.demo

clean:
	rm -rf site .pytest_cache .ruff_cache **/__pycache__
