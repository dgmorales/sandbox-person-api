#!/usr/bin/env python

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class User(BaseModel):
    nome: str
    sobrenome: str
    CPF: str
    email: str
    data: str


database = [
    User(nome="teste1", sobrenome="testado1", CPF="999.999.999-99",
         email="teste1@hotmail.com", data="04/04/1994"),
    User(nome="teste2", sobrenome="testado2", CPF="111.111.111-11",
         email="teste2@hotmail.com", data="03/03/1999")
]


@app.get("/users")
def get_users():
    return database


@app.post("/users/insert_user")
def insert_user(user: User):
    database.append(user)
    return user


@app.get("/users/{CPF_user}")
def get_user_cpf(CPF_user: str):
    for user in database:
        if(user.CPF == CPF_user):
            return user
