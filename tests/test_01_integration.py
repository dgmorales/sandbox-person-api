import random

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pymongo import MongoClient
from time import sleep

from personapi.api import app

pytest_plugins = ["docker_compose"]


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


# def test_user_post():
#     response = client.post("/users", json=new_user)
#     assert response.status_code == status.HTTP_201_CREATED
#     response = client.get("/users/" + new_user['cpf'])
#     assert response.status_code == status.HTTP_200_OK
#     assert response.json() == new_user

@pytest.fixture(scope="module")
def wait_for_db(module_scoped_container_getter):
    service = module_scoped_container_getter.get("person-db").network_info[0]
    for i in range(15):
        try:
            client = MongoClient('mongodb://%s:%s/' %
                                 (service.hostname, service.host_port))
            print('Mongo is up')
            return
        except Exception as e:
            print(e)
            print("Database is not available. Sleep for 1 sec")
            sleep(1)


@pytest.fixture(scope="module")
def testclient(wait_for_db):
    return TestClient(app)


def test_user_post_duplicate(testclient):
    response = testclient.post("/users", json=duplicate_user)
    assert response.status_code == status.HTTP_409_CONFLICT


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
