import random
from datetime import date, timedelta

from personapi.store import User
from personapi.utils import SingletonMeta
from pydantic import ValidationError
from pytest import raises

from .testdata import duplicate_user, new_user, nonexistent_user, users


def test_singleton():
    class TestSingleton(metaclass=SingletonMeta):
        def __init__(self):
            self.myid = random.randint(0, 1000)

    a = TestSingleton()
    b = TestSingleton()
    assert a == b
    assert a.myid == b.myid


def test_new_user():
    User(**new_user)


def test_duplicate_user():
    User(**duplicate_user)


def test_nonexistent_user():
    User(**nonexistent_user)


def test_users():
    for user in users:
        User(**user)


def test_invalid_email():
    invalid_user = new_user.copy()
    invalid_emails = [
        "not-a-email",
        "someone@rootdomain",
        "someone @gmail.com",
    ]
    for item in invalid_emails:
        invalid_user["email"] = item
        # print(item)
        with raises(ValidationError):
            User(**invalid_user)


def test_invalid_birthdate_fmt():
    invalid_user = new_user.copy()
    invalid_dates = [
        "",
        "22/01/1979",
        "22-01-1979",
        "0000-00-00",
        "2000-02-30",
        "2000-13-01",
        "2000-13-01",
        "2000-12-01 00:00",
    ]  # date must be in format YYYY-MM-DD (int & floats converted to unix time)
    for item in invalid_dates:
        invalid_user["birthDate"] = item
        # print(item)
        with raises(ValidationError):
            User(**invalid_user)


def test_birthdate_on_future():
    invalid_user = new_user.copy()
    tomorrow = date.today() + timedelta(days=1)
    invalid_user["birthDate"] = tomorrow.strftime("%Y-%m-%d")
    with raises(ValidationError):
        User(**invalid_user)


def test_invalid_cpf():
    invalid_user = new_user.copy()
    invalid_cpfs = [
        "000.000.000-00",
        "000.000.001-11",
        "123.456.789-00",
        "999.999.999-99",
    ]
    for item in invalid_cpfs:
        invalid_user["cpf"] = item
        # print(item)
        with raises(ValidationError):
            User(**invalid_user)
