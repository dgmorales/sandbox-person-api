#!/usr/bin/env python

from typing import Any, Dict, List, Optional, Union

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from .auth import AuthError, AuthProvider, Token
from .store import User, UserInDB, UserStore
from .utils import Settings

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

token_url = "token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=token_url)


def get_settings():  # pragma: no cover - this is overridden in tests
    # using Depends(Settings) for some reason breaks reading the setting from
    # envvar, so we have this function
    return Settings()


async def get_user_store(settings: Settings = Depends(get_settings)):
    return UserStore(settings.db_conn_str, settings.simulated_delay_seconds)


def get_auth_provider(
    settings: Settings = Depends(get_settings),
    user_store: UserStore = Depends(get_user_store),
):
    return AuthProvider(
        settings.auth_token_base_secret,
        settings.auth_token_algorithm,
        settings.auth_token_expiration_in_minutes,
        user_store,
    )


async def validate_token(
    auth: AuthProvider = Depends(get_auth_provider),
    token: str = Depends(oauth2_scheme),
) -> UserInDB:
    try:
        user = await auth.validate_token(token)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials: %s" % exc,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_existing_user(user_store: UserStore, cpf: str) -> User:
    user = await user_store.get(cpf)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message_for_user_not_found,
        )
    return user


@app.post("/%s" % token_url, response_model=Token)
async def login_for_access_token(
    auth: AuthProvider = Depends(get_auth_provider),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    try:
        token = await auth.auth_user(form_data.username, form_data.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password: %s" % repr(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


@app.get("/users", response_model=List[User])
async def users_get_all(user_store: UserStore = Depends(get_user_store)):
    return await user_store.get_all()


@app.get("/users/me", response_model=User)
async def auth_test(user: str = Depends(validate_token)):
    return user


@app.get("/users/{cpf}", response_model=User, responses=response_ok_or_notfound)
async def users_get_one(cpf: str, user_store: UserStore = Depends(get_user_store)):
    return await get_existing_user(user_store, cpf)


@app.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    responses={
        status.HTTP_201_CREATED: {"model": User},
        status.HTTP_409_CONFLICT: {
            "model": HTTPError,
            "description": "Processing Error: " + error_message_for_duplicate_user,
        },
    },
)
async def users_post(user: User, user_store: UserStore = Depends(get_user_store)):
    if await user_store.get(user.cpf):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error_message_for_duplicate_user,
        )
    await user_store.add(user)
    return user


@app.put(
    "/users/{cpf}",
    response_model=User,
    responses=response_ok_or_notfound
    | {
        status.HTTP_400_BAD_REQUEST: {
            "model": HTTPError,
            "description": "Processing Error: " + error_message_for_cpf_mismatch,
        },
    },
)
async def users_put(
    cpf: str, user: User, user_store: UserStore = Depends(get_user_store)
):
    if cpf != user.cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message_for_cpf_mismatch,
        )

    # will throw exception if user does not exist
    await get_existing_user(user_store, cpf)
    await user_store.update(cpf, user)
    return user


@app.delete("/users/{cpf}", response_model=User, responses=response_ok_or_notfound)
async def users_delete(cpf: str, user_store: UserStore = Depends(get_user_store)):
    # will throw exception if user does not exist
    user = await get_existing_user(user_store, cpf)
    await user_store.remove(cpf)
    return user


if __name__ == "__main__":  # pragma: no cover
    uvicorn.run(app, host="127.0.0.1", port=8000)
