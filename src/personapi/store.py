#!/usr/bin/env python

import os
from datetime import date, datetime

from asyncio import sleep
from typing import Dict, List, Union
from bradocs4py import CPF
from fastapi import Depends
from pydantic import BaseModel, BaseSettings, EmailStr, validator
from motor.motor_asyncio import AsyncIOMotorClient

# hard coded limit for th sake of laziness and not implementing pagination
MAX_USERS = 100


class User(BaseModel):
    firstName: str
    lastName: str
    cpf: str
    email: EmailStr
    birthDate: date

    @validator("cpf")
    def cpf_validator(cls, cpf_str):
        cpf = CPF(cpf_str)
        # not declaring the field itself as CPF type to avoid fuzz with pymongo
        if cpf.isValid:
            return str(cpf)
        else:
            raise ValueError("%s is not a valid CPF number." % cpf_str)

    @validator("birthDate")
    def birth_date_validator(cls, d):
        if d > date.today():
            raise ValueError("Birth date is on the future. Not allowed.")
        # convert to datetime to avoid problems with pymongo
        return datetime(d.year, d.month, d.day)

    class Config:
        json_encoders = {
            # represent as date only to json
            datetime: lambda v: v.strftime("%Y-%m-%d"),
        }
        schema_extra = {
            "example": {
                "firstName": "Mickey",
                "lastName": "Mouse",
                "cpf": "609.350.354-27",
                "email": "mickey.mouse@disney.com",
                "birthDate": "1928-11-18",
            }
        }


class Settings(BaseSettings):
    db_conn_str: str = "mongodb://localhost:27017/"
    simulated_delay_seconds: int = 0


def get_settings():  # pragma: no cover - this is overridden in tests
    # using Depends(Settings) for some reason breaks reading the setting from
    # envvar, so we have this function
    return Settings()


async def get_user_store(settings: Settings = Depends(get_settings)):
    return UserStore(settings.db_conn_str, settings.simulated_delay_seconds)


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


class UserStore(metaclass=SingletonMeta):
    def __init__(self, conn_string: str, simulated_delay_seconds=0):
        print("[PID %d] Connecting to %s" % (os.getpid(), conn_string))
        self.client = AsyncIOMotorClient(conn_string)
        self.db = self.client["people"]
        self.simulated_delay_seconds = simulated_delay_seconds
        print("[PID %d] New MongoDB connection opened." % os.getpid())

    async def add(self, user: User) -> None:
        "Inserts user into the database."
        await self.db.users.insert_one(dict(user))

    async def update(self, cpf: str, user: User) -> None:
        "Updates user with specified cpf."
        await self.db.users.replace_one({"cpf": cpf}, user.dict())

    async def remove(self, cpf: str) -> None:
        "Deletes user with specified cpf."
        await self.db.users.delete_one({"cpf": cpf})

    async def get(self, cpf: str) -> Union[User, None]:
        "Get user with specified cpf. Returns None if not found."
        if self.simulated_delay_seconds > 0:
            await sleep(self.simulated_delay_seconds)  # pragma: no cover
        user = await self.db.users.find_one({"cpf": cpf})
        if user:
            return User(**user)
        else:
            return None

    async def get_all(self) -> List[User]:
        "Get a list of all users."
        # this would not be wise on a huge db (loads all db in memory at once),
        # but will suffice here
        # TODO: fix the hard-coded max here
        users = await self.db.users.find().to_list(MAX_USERS)
        return [User(**u) for u in users]
