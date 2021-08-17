#!/usr/bin/env python

import uvicorn

from typing import List, Dict, Union, Optional, Any
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel

from .store import UserStore, User, get_db


app = FastAPI(
    title="Person API", description="A toy project, a CRUD for people records."
)


class HTTPError(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "Description of the error condition."},
        }


error_message_for_duplicate_user = "Duplicate user. The CPF is already registered."
error_message_for_cpf_mismatch = "CPF in the path does not match CPF in body."
error_message_for_user_not_found = "User does not exist."
response_ok_or_notfound: Optional[Dict[Union[int, str], Dict[str, Any]]] = {
    status.HTTP_200_OK: {"model": User},
    status.HTTP_404_NOT_FOUND: {
        "model": HTTPError,
        "description": error_message_for_user_not_found,
    },
}


async def get_existing_user(db: UserStore, cpf: str) -> User:
    user = await db.get_user(cpf)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message_for_user_not_found,
        )
    return user


@app.get("/users", response_model=List[User])
async def get_users(db: UserStore = Depends(get_db)):
    return await db.get_all_users()


@app.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"model": User},
        status.HTTP_409_CONFLICT: {
            "model": HTTPError,
            "description": "Processing Error: " + error_message_for_duplicate_user,
        },
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


@app.put(
    "/users/{cpf}",
    responses=response_ok_or_notfound
    | {
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Processing Error: " + error_message_for_cpf_mismatch,
        },
    },
)
async def put_user(cpf: str, user: User, db: UserStore = Depends(get_db)):
    if cpf != user.cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message_for_cpf_mismatch,
        )

    # will throw exception if user does not exist
    await get_existing_user(db, cpf)
    await db.update_user(cpf, user)
    return user


@app.get("/users/{cpf}", responses=response_ok_or_notfound)
async def get_user(cpf: str, db: UserStore = Depends(get_db)):
    return await get_existing_user(db, cpf)


@app.delete("/users/{cpf}", responses=response_ok_or_notfound)
async def delete_user(cpf: str, db: UserStore = Depends(get_db)):
    # will throw exception if user does not exist
    user = await get_existing_user(db, cpf)
    await db.delete_user(cpf)
    return user


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
