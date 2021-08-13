import copy

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from pymongo import MongoClient
from time import sleep

from personapi.api import app
from personapi.store import Settings, get_settings

pytest_plugins = ["docker_compose"]

users = [
    {
        "firstName": "Mickey",
        "lastName": "Mouse",
        "cpf": "609.350.354-27",
        "email": "mickey.mouse@disney.com",
        "birthDate": "1928-11-18",
    },
    {
        "firstName": "Minnie",
        "lastName": "Mouse",
        "cpf": "673.810.785-46",
        "email": "minnie.mouse@disney.com",
        "birthDate": "1928-11-18",
    },
]

duplicate_user = {
    "firstName": "Mickey",
    "lastName": "Mouse Python Test",
    "cpf": "609.350.354-27",
    "email": "mickey.mouse2@disney.com",
    "birthDate": "2021-07-10",
}

new_user = {
    "firstName": "Donald",
    "lastName": "Duck",
    "cpf": "324.453.314-04",
    "email": "donald.duck@disney.com",
    "birthDate": "1934-06-09",
}


# should be different from nonexistent user cpf
mismatched_nonexistent_user_cpf = "446.153.595-94"
nonexistent_user = {
    "firstName": "Nonexistent",
    "lastName": "User",
    "cpf": "857.545.040-98",
    "email": "nonexistent@test.com",
    "birthDate": "1980-04-04",
}


@pytest.fixture(scope="module")
def testdb(module_scoped_container_getter):
    """Returns the connection string to a db running on docker compose.

    - Spins up a test db with docker compose
    - Wait for it to be up
    - Prime it with initial data
    - Returns the conn string to it
    """
    service = module_scoped_container_getter.get("person-db").network_info[0]
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
