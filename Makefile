build:
	docker build -t python-person-api:latest .

run:
	docker run --name python-person-api -p 8000:8000 -d python-person-api

down:
	docker stop python-person-api
	docker rm python-person-api