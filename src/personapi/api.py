#!/usr/bin/env python

import uvicorn

from fastapi import FastAPI, HTTPException, Depends, status

from .store import UserStore, User, get_db, user_from_db


app = FastAPI()


@app.get("/users")
def get_users(db: UserStore = Depends(get_db)):
    return [user_from_db(item) for item in db.get_all_users()]


@app.post("/users", status_code=status.HTTP_201_CREATED)
def post_user(user: User, db: UserStore = Depends(get_db)):
    if db.get_user(user.cpf):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate user. The CPF is already registered.",
        )
    db.insert_user(user)
    return user


@app.put("/users/{cpf}")
def put_user(cpf: str, user: User, db: UserStore = Depends(get_db)):
    if cpf != user.cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF in the path does not match CPF in body.",
        )

    if not db.get_user(cpf):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist."
        )
    db.update_user(cpf, user)
    return user


@app.get("/users/{cpf}")
def get_user(cpf: str, db: UserStore = Depends(get_db)):
    u = db.get_user(cpf)
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist."
        )
    return user_from_db(u)


@app.delete("/users/{cpf}")
def delete_user(cpf: str, db: UserStore = Depends(get_db)):
    u = db.get_user(cpf)
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist."
        )
    else:
        db.delete_user(cpf)
    return user_from_db(u)


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
