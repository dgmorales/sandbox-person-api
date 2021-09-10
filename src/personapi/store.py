#!/usr/bin/env python

import os
from asyncio import sleep
from datetime import date, datetime
from typing import List, Optional, Union

from bradocs4py import CPF
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, validator

from .utils import SingletonMeta

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


class UserInDB(User):
    isAdmin: Optional[bool] = False
    hashedPassword: Optional[str] = None


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

    async def get(self, cpf: str) -> Union[UserInDB, None]:
        "Get user with specified cpf. Returns None if not found."
        if self.simulated_delay_seconds > 0:
            await sleep(self.simulated_delay_seconds)  # pragma: no cover
        user = await self.db.users.find_one({"cpf": cpf})
        if user:
            return UserInDB(**user)
        else:
            return None

    async def get_all(self) -> List[UserInDB]:
        "Get a list of all users."
        # this would not be wise on a huge db (loads all db in memory at once),
        # but will suffice here
        # TODO: fix the hard-coded max here
        users = await self.db.users.find().to_list(MAX_USERS)
        return [UserInDB(**u) for u in users]
