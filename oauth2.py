from pydantic import BaseModel
import jwt
import datetime

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
            "roles": ["Manager", "Developer"],
            "disabled": False,
        }
    }

    def __str__(self) -> str:
        return self.users_db 

import datetime
import jwt 

class Autenticator:
    SECRET_KEY = "588d27e4efad58a4260b8de9d12262467df10316ecf38d6c42d5202909d89c0b"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 3

    @classmethod
    def authentication(cls,db, username: str, password: str | None = None):
        user = db.get(username)
        if not username in db or not password in [user['hashed_password'],None]:
            return False
        return user 

    @classmethod
    def create_access_token(cls,data: dict, timezone, expires_delta: datetime.timedelta = 3600):
        to_encode = {}
        to_encode.update({"sub": data.get("username")})
        to_encode.update({"roles": data.get("roles")})
        expire = datetime.datetime.now(timezone) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, Autenticator.SECRET_KEY, algorithm=Autenticator.ALGORITHM)
        return encoded_jwt
