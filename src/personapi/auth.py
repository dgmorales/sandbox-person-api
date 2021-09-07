#!/usr/bin/env python
"""
Auth support for the Person API
"""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .store import UserInDB, UserStore
from .utils import SingletonMeta


class AuthError(Exception):
    pass


class TokenValidationError(AuthError):
    pass


class InvalidUser(AuthError):
    pass


class WrongPassword(AuthError):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str


class AuthProvider(metaclass=SingletonMeta):
    def __init__(
        self,
        token_base_secret: str,
        token_algorithm: str,
        token_expiration_in_minutes: int,
        user_store: UserStore,
    ):
        self.token_base_secret = token_base_secret
        self.token_algorithm = token_algorithm
        self.auth_token_expiration_in_minutes = token_expiration_in_minutes
        self.user_store = user_store

        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def auth_user(self, username: str, password: str) -> Token:
        user = await self.user_store.get(username)
        if not user:
            raise InvalidUser("Cannot find '%s' user" % username)
        elif not user.isAdmin:
            raise InvalidUser(
                "User '%s' is not an admin. User must be an Admin to be allowed access."
                % username
            )
        elif not self._verify_password(password, user.hashedPassword):
            raise WrongPassword
        else:
            return self._create_access_token(data={"sub": user.cpf})

    async def validate_token(self, token: str) -> UserInDB:
        try:
            payload = jwt.decode(
                token, self.token_base_secret, algorithms=self.token_algorithm
            )
            username: str = payload.get("sub")
            if username is None:
                return TokenValidationError("Token does not specify user")
            token_data = TokenData(username=username)
        except JWTError:
            raise TokenValidationError("Error decoding token")

        user = await self.user_store.get(token_data.username)
        if user is None:
            raise TokenValidationError("User not found")

        return user

    def _create_access_token(self, data: dict) -> Token:
        "Generates an access Token using JWT"
        to_encode = data.copy()

        expiration_time = datetime.utcnow() + timedelta(
            minutes=self.auth_token_expiration_in_minutes
        )
        to_encode.update({"exp": expiration_time})

        encoded_jwt = jwt.encode(
            to_encode, self.token_base_secret, algorithm=self.token_algorithm
        )
        return Token(access_token=encoded_jwt, token_type="bearer")

    def _verify_password(self, plain_password, hashed_password):
        return self.pwd_context.verify(plain_password, hashed_password)

    def _get_password_hash(self, password):
        return self.pwd_context.hash(password)
