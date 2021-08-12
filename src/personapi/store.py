#!/usr/bin/env python

import os
from pymongo import MongoClient
from pydantic import BaseModel, BaseSettings
from fastapi import Depends


class User(BaseModel):
    firstName: str
    lastName: str
    cpf: str
    email: str
    birthDate: str


class Settings(BaseSettings):
    db_conn_str: str = "mongodb://localhost:27017/"


def get_settings():  # pragma: no cover - this is overridden in tests
    # using Depends(Settings) for some reason breaks reading the setting from
    # envvar, so we have this function
    return Settings()


def get_db(settings: Settings = Depends(get_settings)):
    return UserStore(settings.db_conn_str)


def user_from_db(user_db_item):
    """Transform a mongo document on a User class object.

    A hack while I do not understand enough of fastapi and pydantic to do it better."
    """
    return User(
        firstName=user_db_item["firstName"],
        lastName=user_db_item["lastName"],
        cpf=user_db_item["cpf"],
        email=user_db_item["email"],
        birthDate=user_db_item["birthDate"],
    )


# thread unsafe singleton from https://refactoring.guru/design-patterns/singleton/python
class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class UserStore(metaclass=SingletonMeta):
    def __init__(self, conn_string):
        print("[PID %d] Connecting to %s" % (os.getpid(), conn_string))
        self.client = MongoClient(conn_string)
        self.db = self.client["people"]
        print("[PID %d] New MongoDB connection opened." % os.getpid())

    def insert_user(self, user):
        self.db.users.insert_one(dict(user))

    def update_user(self, cpf, user):
        self.db.users.replace_one({"cpf": cpf}, dict(user))

    def delete_user(self, cpf):
        self.db.users.delete_one({"cpf": cpf})

    def get_user(self, cpf):
        return self.db.users.find_one({"cpf": cpf})

    def get_all_users(self):
        # this would not be wise on a huge db (loads all db in memory at once),
        # but will suffice here
        return list(self.db.users.find())
