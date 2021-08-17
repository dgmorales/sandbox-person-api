import copy
from time import sleep

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from personapi.api import app
from personapi.store import Settings, get_settings
from pymongo import MongoClient

from .testdata import (
    duplicate_user,
    mismatched_nonexistent_user_cpf,
    new_user,
    nonexistent_user,
    users,
)

pytest_plugins = ["docker_compose"]


@pytest.fixture(scope="module")
def testdb(module_scoped_container_getter):
    """Returns the connection string to a db running on docker compose.

    - Spins up a test db with docker compose
    - Wait for it to be up
    - Prime it with initial data
    - Returns the conn string to it
    """
    service = module_scoped_container_getter.get("person-db-test").network_info[0]
    db_conn_str = "mongodb://%s:%s/" % (service.hostname, service.host_port)
    for i in range(15):
        try:
            client = MongoClient(db_conn_str)
            print("Mongo is up")
            # prime db
            # must deepcopy because insert_many changes the dict objects inserting _id
            client["people"].users.insert_many(copy.deepcopy(users))
            return db_conn_str
        except Exception as e:
            print(e)
            print("Database is not available. Sleep for 1 sec")
            sleep(1)
    return None  # should throw error


@pytest.fixture(scope="module")
def testclient(testdb):
    def get_test_settings():
        "Function to override settings using the conn string returned by testdb fixture"
        return Settings(db_conn_str=testdb)

    app.dependency_overrides[get_settings] = get_test_settings
    return TestClient(app)


def test_get_users(testclient):
    print(users)
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
