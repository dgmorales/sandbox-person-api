#!/usr/bin/env python

import uvicorn

from typing import List
from fastapi import FastAPI, HTTPException, Depends, status

from .store import UserStore, User, get_db, user_from_db


app = FastAPI(
    title="Person API", description="A toy project, a CRUD for people records."
)


@app.get("/users", response_model=List[User])
async def get_users(db: UserStore = Depends(get_db)):
    return [user_from_db(item) for item in await db.get_all_users()]


error_message_for_duplicate_user = "Duplicate user. The CPF is already registered."


@app.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Processing Error: " + error_message_for_duplicate_user
        }
    },
)
async def post_user(user: User, db: UserStore = Depends(get_db)):
    if await db.get_user(user.cpf):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_message_for_duplicate_user,
        )
    await db.insert_user(user)
    return user


@app.put("/users/{cpf}", response_model=User)
async def put_user(cpf: str, user: User, db: UserStore = Depends(get_db)):
    if cpf != user.cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF in the path does not match CPF in body.",
        )

    if not await db.get_user(cpf):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist."
        )
    await db.update_user(cpf, user)
    return user


@app.get("/users/{cpf}", response_model=User)
async def get_user(cpf: str, db: UserStore = Depends(get_db)):
    u = await db.get_user(cpf)
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist."
        )
    return user_from_db(u)


@app.delete("/users/{cpf}", response_model=User)
async def delete_user(cpf: str, db: UserStore = Depends(get_db)):
    u = await db.get_user(cpf)
    if not u:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist."
        )
    else:
        await db.delete_user(cpf)
    return user_from_db(u)


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
