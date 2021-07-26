#!/usr/bin/env python

import os
from pymongo import MongoClient


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
        self.client = MongoClient(conn_string)
        print("[PID %d] New MongoDB connection opened." % os.getpid())
        self.db = self.client['people']

    def insert_user(self, user):
        self.db.users.insert_one(dict(user))

    def update_user(self, cpf, user):
        self.db.users.replace_one({"cpf": cpf}, dict(user))

    def delete_user(self, cpf):
        self.db.users.delete_one({"cpf": cpf})

    def get_user(self, cpf):
        return self.db.users.find_one({"cpf": cpf})

    def get_all_users(self):
        # this would not be wise on a huge db (loads all db in memory at once), but will suffice here
        return list(self.db.users.find())
