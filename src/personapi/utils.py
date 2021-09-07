#!/usr/bin/env python
"""
Supporting functions and classes shared by other modules in the Person API package.
"""
from typing import Dict

from pydantic import BaseSettings


class Settings(BaseSettings):
    db_conn_str: str = "mongodb://localhost:27017/"
    simulated_delay_seconds: int = 0
    auth_token_algorithm: str = "HS256"
    auth_token_expiration_in_minutes: int = 15
    auth_token_base_secret: str

    class Config:
        env_prefix = "personapi_"


# thread unsafe singleton from https://refactoring.guru/design-patterns/singleton/python
class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances: Dict[type, type] = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
