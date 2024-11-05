from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
import datetime
from datetime import timezone

# Modelo de usuario y token
class User(BaseModel):
    username: str
    full_name: str | None = None
    email: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class DataBase():
    users_db = {
        "edscrimaglia": {
            "username": "edscrimaglia",
            "full_name": "Edgardo Scrimaglia",
            "email": "edscrimaglia@octupus.com",
            "hashed_password": "Iaew-2024$",
            "disabled": False,
        }
    }

    def __str__(self) -> str:
        return self.users_db 

import datetime
import jwt 

class Autenticator:
    SECRET_KEY = "mi_clave_secreta"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30

    @classmethod
    def authentication(cls,db, username: str, password: str | None = None):
        user = db.get(username)
        if not username in db or not password in [user['hashed_password'],None]:
            return False
        return user 

    @classmethod
    def create_access_token(cls,data: dict, timezone, expires_delta: datetime.timedelta = 3600):
        to_encode = data.copy()
        expire = datetime.datetime.now(timezone) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, Autenticator.SECRET_KEY, algorithm=Autenticator.ALGORITHM)
        return encoded_jwt

    @classmethod
    def validate_expiration(cls, payload: dict):
        expiration_timestamp = payload.get('exp')
        
        if expiration_timestamp is None:
            raise ValueError("Expiration timestamp 'exp' no esxiste en el payload")
        
        #exp_time = datetime.datetime.fromtimestamp(expiration_timestamp, tz=timezone)
        exp_time = exp_datetime = datetime.datetime.fromtimestamp(expiration_timestamp, datetime.timezone.utc)
        #now_time_zone = datetime.datetime.now().replace(tzinfo=timezone)
        now_time = datetime.datetime.now(datetime.timezone.utc)
        if exp_datetime <= now_time:
            return True
        return False