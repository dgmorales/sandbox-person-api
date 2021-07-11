#!/usr/bin/env python

import os
from fastapi import FastAPI
from pydantic import BaseModel
from person_store import UserStore

DB_CONN_STR = os.environ['DB_CONN_STR']
# "mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/myFirstDatabase"

app = FastAPI()
db = UserStore(DB_CONN_STR)


class User(BaseModel):
    firstName: str
    lastName: str
    cpf: str
    email: str
    birthDate: str


def user_from_db(user_db_item):
    """ Transform a mongo document on a User class object.

    A hack while I do not understand enough of fastapi and pydantic to do it better."
    """
    return User(firstName=user_db_item['firstName'],
                lastName=user_db_item['lastName'],
                cpf=user_db_item['cpf'],
                email=user_db_item['email'],
                birthDate=user_db_item['birthDate'],
                )


@app.get("/users")
def get_users():
    return [user_from_db(item) for item in db.get_all_users()]


@app.post("/users/insert_user")
def insert_user(user: User):
    db.insert_user(user)
    return user


@app.get("/users/{cpf}")
def get_user_cpf(cpf: str):
    return user_from_db(db.get_user(cpf))
