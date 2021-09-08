import copy
from time import sleep

import pytest
import subprocess
import secrets
from fastapi import status
from fastapi.testclient import TestClient
from personapi.api import app, get_settings, token_url
from personapi.utils import Settings
from personapi.auth import PasswordHasher
from pymongo import MongoClient

from .testdata import (
    duplicate_user,
    mismatched_nonexistent_user_cpf,
    new_user,
    nonexistent_user,
    users,
)

pytest_plugins = ["docker_compose"]
test_auth_user_index = 0
test_auth_user_password = "SuperPa$sword123"


@pytest.fixture(scope="session", autouse=True)
def check_docker_is_running():
    exit_code = subprocess.call(["docker", "info"])
    if exit_code != 0:
        pytest.exit(
            5, "Docker is not running. It is required to the integration tests. Exiting"
        )


@pytest.fixture(scope="module")
def testdb_conn_str(module_scoped_container_getter):
    """Returns the connection string to a db running on docker compose.

    - Spins up a test db with docker compose
    - Returns the conn string to it
    """
    service = module_scoped_container_getter.get("person-db-test").network_info[0]
    return "mongodb://%s:%s/" % (service.hostname, service.host_port)


@pytest.fixture(scope="module")
def testsettings(testdb_conn_str):
    "Returns app Settings suitable for testing"
    return Settings(
        db_conn_str=testdb_conn_str, auth_token_base_secret=secrets.token_hex()
    )


@pytest.fixture(scope="module")
def testdb_prime_data(testsettings):
    "Returns suitable data for priming the database"
    password_hasher = PasswordHasher()
    users_with_auth_info = copy.deepcopy(users)
    users_with_auth_info[test_auth_user_index].update(
        {
            "isAdmin": True,
            "hashedPassword": password_hasher.get_hash(test_auth_user_password),
        }
    )
    return users_with_auth_info


@pytest.fixture(scope="module")
def testdb_primed(testdb_conn_str, testdb_prime_data):
    """Primes the database with data.

    - Wait for the db to be up
    - Prime it with initial data
    - Returns the conn string to it
    """
    for i in range(15):
        try:
            client = MongoClient(testdb_conn_str)
            print("Mongo is up")
            # prime db
            # must deepcopy because insert_many changes the dict objects inserting _id
            print(testdb_prime_data)
            client["people"].users.insert_many(testdb_prime_data)
            return testdb_conn_str
        except Exception as e:
            print(e)
            print("Database is not available. Sleep for 1 sec")
            sleep(1)
    return None  # should throw error


@pytest.fixture(scope="module")
def testclient(testdb_primed, testsettings):
    def get_test_settings():
        return testsettings

    app.dependency_overrides[get_settings] = get_test_settings
    return TestClient(app)


@pytest.fixture(scope="module")
def testtoken(testclient):
    auth_data = {
        "grant_type": "password",
        "username": users[test_auth_user_index]["cpf"],
        "password": test_auth_user_password,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = testclient.post("/%s" % token_url, headers=headers, data=auth_data)
    if response.status_code == status.HTTP_200_OK:
        print(response)
        print(dir(response))
        return response.json()


def test_get_users(testclient):
    response = testclient.get("/users/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(users)


def test_get_user(testclient):
    user = users[0]
    response = testclient.get("/users/" + user["cpf"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user


def test_user_post_get_delete(testclient):
    response = testclient.post("/users", json=new_user)
    assert response.status_code == status.HTTP_201_CREATED
    response = testclient.get("/users/" + new_user["cpf"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == new_user
    response = testclient.delete("/users/" + new_user["cpf"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == new_user


def test_user_post_duplicate(testclient):
    response = testclient.post("/users", json=duplicate_user)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_user_put(testclient):
    user = users[0]
    user["lastName"] += " Changed"
    response = testclient.put("/users/" + user["cpf"], json=user)
    assert response.status_code == status.HTTP_200_OK

    response = testclient.get("/users/" + user["cpf"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user


def test_user_put_nonexistent(testclient):
    # should we accept it and treat the same as a POST?
    # for now, we don't

    response = testclient.put(
        "/users/" + nonexistent_user["cpf"], json=nonexistent_user
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_put_mismatch(testclient):
    # should we pass the CPF both on the request path and body?
    # for now, we do, and must return an error if they differ

    # this asserts the test sanity itself
    assert mismatched_nonexistent_user_cpf != nonexistent_user["cpf"]

    response = testclient.put(
        "/users/" + mismatched_nonexistent_user_cpf, json=nonexistent_user
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_get_nonexistent(testclient):
    response = testclient.get("/users/" + nonexistent_user["cpf"])
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_delete_nonexistent(testclient):
    response = testclient.delete("/users/" + nonexistent_user["cpf"])
    assert response.status_code == status.HTTP_404_NOT_FOUND
