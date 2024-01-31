build: requirements.txt
	docker-compose build

build-api: requirements.txt
	docker build -t python-person-api:latest .

run-python:
	NEW_RELIC_CONFIG_FILE=newrelic.ini pipenv run newrelic-admin run-program uvicorn personapi.api:app

requirements.txt: Pipfile
#  We generate requirements from Pipfile, but remove the local package install
# This is done to optimize docker image building, see Dockerfile
	pipenv lock --keep-outdated --requirements | grep -v '^\-e \.' > requirements.txt

tests:
	pipenv run pytest tests/
.PHONY: tests

checks:
	pipenv run flake8
	pipenv run black --check .
	pipenv run bandit -c bandit.yml -qr .

full-check: check run-tests

up:
	docker-compose up

down:
	docker-compose down