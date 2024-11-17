from pydantic import BaseModel
import jwt
import datetime
from fastapi import HTTPException, status

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

class OauthDb():
    users_db = {
        "supervisor": {
            "username": "supervisor",
            "full_name": "Edgardo Scrimaglia",
            "email": "edscrimaglia@octupus.com",
            "hashed_password": "Iaew-2024$",
            "roles": ["manager", "developer", "operator"],
            "disabled": False,
        },
        "operator": {
            "username": "operator",
            "full_name": "System Operator",
            "email": "operator@octupus.com",
            "hashed_password": "Iaew-2024$",
            "roles": ["operator"],
            "disabled": False,
        }
    }

    api_registration = {
        "/api/v1/pedido": {
            "roles": ["manager"]
        },
        "/api/v1/costo": {
            "roles": ["manager"]
        },
        "/api/v1/producto": {
            "roles": ["manager"]
        },
        "/api/v1/pedidos": {
            "roles": ["manager", "operator"]
        },
        "/api/v1/producer": {
            "roles": ["manager"]
        }
    }
    

import datetime
import jwt 

class Oauth2:
    def __init__(self, algorithm: str = "HS256",expires: int = 30) -> None:
        self.SECRET_KEY = "588d27e4efad58a4260b8de9d12262467df10316ecf38d6c42d5202909d89c0b"
        self.ALGORITHM = algorithm 
        self.ACCESS_TOKEN_EXPIRE_MINUTES = expires


    def raise_credentials_exception(self, status: int, detail: str) -> HTTPException:
        raise HTTPException(
            status_code=status,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    

    def authentication(self, username: str, password: str | None = None, db: OauthDb = OauthDb.users_db) -> tuple[dict,str]:
        msg = "User Autenticated"
        user_db = db.get(username)
        if user_db is None or not password in [user_db.get('hashed_password'),None]:
            msg =  "Invalid username or password"
            return user_db, msg
        return user_db, msg


    def create_access_token(self, data: dict, timezone, expires_delta: datetime.timedelta = 3600) -> str:
        to_encode = {}
        to_encode.update({"sub": data.get("username")})
        to_encode.update({"roles": data.get("roles")})
        expire = datetime.datetime.now(timezone) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_jwt
    

    def authorization(self, endpoint: str, token: str) -> None:
        def raise_credentials_exception(status: int, detail: str):
            raise HTTPException(
                status_code=status,
                detail=detail,
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not endpoint in OauthDb.api_registration:
            self.raise_credentials_exception(status.HTTP_403_FORBIDDEN, "Invalid Authorization")

        token_data = self.decode_token(token=token)
        user_db, _ = self.authentication(token_data.get("username"))
        if user_db is None:
            raise_credentials_exception(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
        user = OauthDb.users_db.get(token_data.get("username"))
        if not user:
            raise_credentials_exception(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")
        roles = token_data.get("roles")
        
        roles_db = OauthDb.api_registration.get(endpoint).get("roles")
        if len(roles) == 0 or len(set(roles_db).intersection(set(roles))) == 0:
            self.raise_credentials_exception(status.HTTP_403_FORBIDDEN, "Invalid Authorization") 


    def decode_token(self,token) -> dict:
        try:
            token_data = {}
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            username = payload.get("sub")
            roles =  payload.get("roles")
            if username is None:
                self.raise_credentials_exception(status.HTTP_401_UNAUTHORIZED, "Invalid username or password")
            token_data.update({"username":username, "roles": roles})
        except (jwt.PyJWTError, jwt.ExpiredSignatureError) as error:
            self.raise_credentials_exception(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials")
        
        return token_data
