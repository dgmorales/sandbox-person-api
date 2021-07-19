import random

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from person_api import User, app, get_user, post_user, put_user
from person_store import SingletonMeta

client = TestClient(app)
TEST_URL = 'http://localhost:8000'

duplicate_user = User(
    firstName="Mickey",
    lastName="Mouse Python Test",
    cpf="000.000.0001-11",
    email="mickey.mouse2@disney.com",
    birthDate="04/04/1965")


# should be different from nonexistent user cpf
mismatched_nonexistent_user_cpf = "999.999.9999-99"
nonexistent_user = User(
    firstName="Nonexistent",
    lastName="User",
    cpf="000.000.0000-00",
    email="nonexistent@test.com",
    birthDate="04/04/1980")


def test_singleton():
    class TestSingleton(metaclass=SingletonMeta):
        def __init__(self):
            self.myid = random.randint(0, 1000)

    a = TestSingleton()
    b = TestSingleton()
    assert(a == b)
    assert(a.myid == b.myid)


def test_user_post_duplicate():
    with pytest.raises(HTTPException) as e_info:
        post_user(duplicate_user)
    assert e_info.value.status_code == status.HTTP_409_CONFLICT


def test_user_put_nonexistent():
    # should we accept it and treat the same as a POST?
    # for now, we don't

    with pytest.raises(HTTPException) as e_info:
        put_user(nonexistent_user.cpf, nonexistent_user)
    assert e_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_user_put_mismatch():
    # should we pass the CPF both on the request path and body?
    # for now, we do, and must return an error if they differ

    # this asserts the test sanity itself
    assert mismatched_nonexistent_user_cpf != nonexistent_user.cpf

    with pytest.raises(HTTPException) as e_info:
        put_user(mismatched_nonexistent_user_cpf, nonexistent_user)
    assert e_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_user_get_nonexistent():
    with pytest.raises(HTTPException) as e_info:
        get_user(nonexistent_user.cpf)
    assert e_info.value.status_code == status.HTTP_404_NOT_FOUND
