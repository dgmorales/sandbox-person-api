FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

EXPOSE 8000/tcp
ENV NEW_RELIC_CONFIG_FILE=newrelic.ini 

RUN pip install newrelic
COPY . /app
WORKDIR /app
CMD newrelic-admin run-program uvicorn --host 0.0.0.0 person-api:app