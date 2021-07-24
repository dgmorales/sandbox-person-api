build: requirements.txt
	docker compose build

build-api: requirements.txt
	docker build -t python-person-api:latest .

run-python:
	NEW_RELIC_CONFIG_FILE=newrelic.ini pipenv run newrelic-admin run-program uvicorn personapi.api:app

requirements.txt: Pipfile
	pipenv lock --keep-outdated --requirements > requirements.txt

run-tests:
	pipenv run pytest tests/

up:
	docker compose up

down:
	docker compose down