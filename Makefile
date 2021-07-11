build:
	cd python-person-api; pipenv lock --keep-outdated --requirements > requirements.txt
	docker compose build

build-api:
	cd python-person-api; pipenv lock --keep-outdated --requirements > requirements.txt
	cd python-person-api; docker build -t python-person-api:latest .

run:
	cd python-person-api; docker run --name python-person-api -p 8000:8000 -d python-person-api

run-python:
	cd python-person-api; NEW_RELIC_CONFIG_FILE=newrelic.ini pipenv run newrelic-admin run-program uvicorn person_api:app

up:
	docker compose up

down:
	docker compose down

down-api:
	docker stop python-person-api
	docker rm python-person-api