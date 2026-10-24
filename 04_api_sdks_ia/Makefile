.PHONY: install run dev run_clase_1 debug_clase_1 run_clase_4 run_clase_5 test_clase_5 docker_up build_clase_5 docker_run_clase_5 eval_clase_5 eval_clase_5_real

install:
	uv venv .venv --python 3.11 --allow-existing
	uv pip install -r requirements.txt --python .venv/bin/python

run:
	.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 4200

dev:
	.venv/bin/uvicorn app.main:app --reload --reload-dir=app --host 127.0.0.1 --port 4200

run_clase_1:
	cd clase_01 && ../.venv/bin/python main.py

run_clase_4:
	cd Clases/04 && ../../.venv/bin/uvicorn app:app --reload --port 4200

run_clase_5:
	cd Clases/05 && ../../.venv/bin/uvicorn app:app --reload --port 4200

test_clase_5:
	cd Clases/05 && ../../.venv/bin/python -m pytest

eval_clase_5:
	cd Clases/05 && ../../.venv/bin/python run_eval.py --mode mock

eval_clase_5_real:
	cd Clases/05 && ../../.venv/bin/python run_eval.py --mode real

docker_up:
	@docker info >/dev/null 2>&1 && echo "Docker daemon already running." || ( \
		echo "Starting Docker Desktop..."; \
		systemctl --user start docker-desktop; \
		for i in $$(seq 1 30); do \
			docker info >/dev/null 2>&1 && exit 0; \
			sleep 2; \
		done; \
		echo "Docker daemon did not become ready in time."; exit 1 \
	)

build_clase_5: docker_up
	docker build -f Clases/05/Dockerfile -t ai-triage-api .
	docker run --rm --env-file Clases/05/.env -p 4200:8000 ai-triage-api

docker_run_clase_5: docker_up
	docker run --rm --env-file Clases/05/.env -p 4200:8000 ai-triage-api
