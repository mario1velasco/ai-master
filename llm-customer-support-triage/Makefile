.PHONY: install dev run test eval eval-real check-keys docker-build docker-run clean

install:
	uv venv .venv --python 3.11 --allow-existing
	uv pip install -r requirements.txt --python .venv/bin/python

dev:
	.venv/bin/uvicorn app.main:app --reload --reload-dir=app --host 127.0.0.1 --port 8100

run:
	.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8100

test:
	.venv/bin/python -m pytest

eval:
	.venv/bin/python -m eval.run_eval --mode mock

eval-real:
	.venv/bin/python -m eval.run_eval --mode real

check-keys:
	.venv/bin/python -m app.scripts.check_keys

docker-build:
	docker build -t triage-api-local .

docker-run:
	docker run --rm --env-file .env -p 8100:8100 triage-api-local

clean:
	rm -rf .venv __pycache__ .pytest_cache outputs logs
