import random
import copy

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pymongo import MongoClient
from time import sleep

from personapi.api import app

pytest_plugins = ["docker_compose"]

users = [
    {
        "firstName": "Mickey",
        "lastName": "Mouse",
        "cpf": "000.000.0001-11",
        "email": "mickey.mouse@disney.com",
        "birthDate": "04/04/1960",
    },
    {
        "firstName": "Minnie",
        "lastName": "Mouse",
        "cpf": "000.000.0002-22",
        "email": "minnie.mouse@disney.com",
        "birthDate": "03/03/1966",
    }
]

duplicate_user = {
    "firstName": "Mickey",
    "lastName": "Mouse Python Test",
    "cpf": "000.000.0001-11",
    "email": "mickey.mouse2@disney.com",
    "birthDate": "04/04/1965",
}

new_user = {
    "firstName": "Donald",
    "lastName": "Duck",
    "cpf": "000.000.0003-33",
    "email": "donald.duck@disney.com",
    "birthDate": "07/09/1970",
}


# should be different from nonexistent user cpf
mismatched_nonexistent_user_cpf = "999.999.9999-99"
nonexistent_user = {
    "firstName": "Nonexistent",
    "lastName": "User",
    "cpf": "000.000.0000-00",
    "email": "nonexistent@test.com",
    "birthDate": "04/04/1980",
}


@pytest.fixture(scope="module")
def ready_db(module_scoped_container_getter):
    service = module_scoped_container_getter.get("person-db").network_info[0]
    for i in range(15):
        try:
            client = MongoClient('mongodb://%s:%s/' %
                                 (service.hostname, service.host_port))
            print('Mongo is up')
            return client
        except Exception as e:
            print(e)
            print("Database is not available. Sleep for 1 sec")
            sleep(1)
    return None


@pytest.fixture(scope="module")
def primed_db(ready_db):
    "Returns a client connection to a database primed with initial data for the tests"
    # must deepcopy because insert_many changes the dict objects inserting _id
    ready_db['people'].users.insert_many(copy.deepcopy(users))
    return ready_db


@pytest.fixture(scope="module")
def testclient(primed_db):
    return TestClient(app)


def test_get_users(testclient):
    print(users)
    response = testclient.get("/users/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == len(users)


def test_get_user(testclient):
    user = users[0]
    response = testclient.get("/users/" + user['cpf'])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user


def test_user_post_get_delete(testclient):
    response = testclient.post("/users", json=new_user)
    assert response.status_code == status.HTTP_201_CREATED
    response = testclient.get("/users/" + new_user['cpf'])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == new_user
    response = testclient.delete("/users/" + new_user['cpf'])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == new_user


def test_user_post_duplicate(testclient):
    response = testclient.post("/users", json=duplicate_user)
    assert response.status_code == status.HTTP_409_CONFLICT


def test_user_put(testclient):
    user = users[0]
    user['lastName'] += " Changed"
    response = testclient.put(
        "/users/" + user['cpf'], json=user)
    assert response.status_code == status.HTTP_200_OK

    response = testclient.get("/users/" + user['cpf'])
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user


def test_user_put_nonexistent(testclient):
    # should we accept it and treat the same as a POST?
    # for now, we don't

    response = testclient.put(
        "/users/" + nonexistent_user['cpf'], json=nonexistent_user)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_put_mismatch(testclient):
    # should we pass the CPF both on the request path and body?
    # for now, we do, and must return an error if they differ

    # this asserts the test sanity itself
    assert mismatched_nonexistent_user_cpf != nonexistent_user['cpf']

    response = testclient.put(
        "/users/" + mismatched_nonexistent_user_cpf, json=nonexistent_user)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_user_get_nonexistent(testclient):
    response = testclient.get("/users/" + nonexistent_user['cpf'])
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_user_delete_nonexistent(testclient):
    response = testclient.delete("/users/" + nonexistent_user['cpf'])
    assert response.status_code == status.HTTP_404_NOT_FOUND
