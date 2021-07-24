#!/usr/bin/env python

import os
import uvicorn


from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from .store import UserStore

if 'DB_CONN_STR' in os.environ:
    DB_CONN_STR = os.environ['DB_CONN_STR']
else:
    # TODO: maybe we should raise an exception here
    DB_CONN_STR = 'mongodb://localhost:27017/'  # default


app = FastAPI()


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
    db = UserStore(DB_CONN_STR)
    return [user_from_db(item) for item in db.get_all_users()]


@app.post("/users", status_code=status.HTTP_201_CREATED)
def post_user(user: User):
    db = UserStore(DB_CONN_STR)
    if db.get_user(user.cpf):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Duplicate user. The CPF is already registered.")
    db.insert_user(user)
    return user


@app.put("/users/{cpf}")
def put_user(cpf: str, user: User):
    db = UserStore(DB_CONN_STR)
    if cpf != user.cpf:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="CPF in the path does not match CPF in body.")

    if not db.get_user(cpf):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist.")
    db.update_user(cpf, user)
    return user


@app.get("/users/{cpf}")
def get_user(cpf: str):
    db = UserStore(DB_CONN_STR)
    u = db.get_user(cpf)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User does not exist.")
    return user_from_db(u)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
