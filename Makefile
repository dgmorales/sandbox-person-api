build: requirements.txt
	nerdctl -n k8s.io compose build

build-api: requirements.txt
	nerdctl -n k8s.io build -t python-person-api/person-api:v0.9.3 .

build-db:
	nerdctl -n k8s.io build -f Dockerfile.db -t python-person-api/person-db:v0.0.1 .

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
	nerdctl compose up

down:
	nerdctl compose down