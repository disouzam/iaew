# FastAPi Educational Proyect

import datetime
import os
import platform
import subprocess
import uuid
from pydantic import AfterValidator, BaseModel
from fastapi import FastAPI, HTTPException, Depends, status, Request
from sqlmodel import Field, SQLModel, create_engine, Session, select
import rabbitmq as rb
from oauth2 import OauthDb, Token, Oauth2
import json
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import pytz
from typing import TypeVar, Annotated, List
from custom_validation import ValidateListToStr
from enum import Enum
import re

local_timezone = pytz.timezone('America/Argentina/Buenos_Aires')
SCRIPT_PATH = "./order_service.py"

# Annotated para usar en ValidateListToStr
T = TypeVar('T')
ValidList = Annotated[list[T], AfterValidator(ValidateListToStr.convert_list_to_str)]

class Estado(Enum):
    Confirmado = "CNF"
    Pendiente = "PND"
    Cancelado = "CAN"

class Producto(BaseModel):
    producto: str = Field(default=uuid.uuid4())
    cantidad: float = Field(..., gt=0)

class ProductoBase(BaseModel):
    producto: ValidList[Producto]
    estado: Estado | None = "CNF" 
    total: float | None = None

class PedidoBase(SQLModel):
    producto: str
    estado: Estado | None = "CNF" 
    total: float | None = None

class Pedido(PedidoBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    userid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    costo: float = Field(default=12.6)
    creacion: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(local_timezone))

class PedidoPrecio(PedidoBase):
    userid: str = Field(default_factory=lambda: str(uuid.uuid4())) 
    costo: float = Field(default=12.6)

class PedidoResponse(BaseModel):
    pedidoId: str = Field(default=str(uuid.uuid4()))
    userId: str = Field(default=str(uuid.uuid4()))
    producto: list[Producto]
    creacion: datetime.datetime = Field(default=lambda: datetime.datetime.now(local_timezone))
    total: float

# Starting FastApi
app = FastAPI(title="IAEW", description="REST Full API TP - Grupo 1 - 2024", version="12.0.0", summary="Use Oauth2 in Postman for Authentication and Authorization")

# Dependencia para el esquema de autenticación
Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Objetos de SQLite y el ORM
sqlite_file_name = "iaew.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)

# Instancing Oauth2
oauth = Oauth2(algorithm="HS256",expires=3)

# API Endpoints
@app.post("/api/v1/pedido", tags=["API Endpoints"])
def create_pedido(request: Request, pedido: ProductoBase, token: str = Depends(Oauth2_scheme)):
    oauth.authorization(request.url.path, token)
    
    def extrae_productos(producto_string: str):
        pattern = re.compile(r"Producto\(producto='(.*?)', cantidad=(.*?)\)")
        return [
            {"producto": match.group(1), "cantidad": float(match.group(2))}
            for match in pattern.finditer(producto_string)
        ]

    def create_db_output(db_pedido, productos):
        return {
            "pedidoId": db_pedido.id,
            "userId": db_pedido.userid,
            "producto": productos,
            "creacion": db_pedido.creacion,
            "total": db_pedido.total
        }
    
    with Session(engine) as session:
        db_pedido = Pedido.model_validate(pedido)
        productos = extrae_productos(db_pedido.producto)
        db_output = create_db_output(db_pedido, productos)
        session.add(db_pedido)
        session.commit()
        session.refresh(db_pedido)
        
        return db_output


@app.post("/api/v1/producer",tags=["RabbitMQ Process"])
def publish_pedido(request: Request, token: str = Depends(Oauth2_scheme)):
    oauth.authorization(request.url.path, token)

    try:
        msg = json.dumps(rb.for_publishing, indent=2)
        result = rb.send_message(msg=msg)
        success, response_message = result
        if not success:
            msg = {"RabbitMQ": response_message}
        else:
            msg = rb.for_publishing
        return msg
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error al decodificar formato JSON")
    except TypeError as err:
        raise HTTPException(status_code=422, detail="Error de tipo: " + str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail="Error: " + str(err))
    

@app.get("/api/v1/pedidos", response_model=list[PedidoResponse], tags=["API Endpoints"])
def read_pedidos(request: Request, token: str = Depends(Oauth2_scheme)) -> List[dict]:
    oauth.authorization(request.url.path, token)

    with Session(engine) as session:
        registros_pedidos = session.exec(select(Pedido)).all()

        def parse_productos(produc: str) -> List[dict]:
            pattern = re.compile(r"Producto\(producto='(.*?)', cantidad=(.*?)\)")
            return [{"producto": match.group(1), "cantidad": float(match.group(2))}
                    for match in pattern.finditer(produc)]
        
        db_output = [{
            "pedidoId": reg.id,
            "userId": reg.userid,
            "producto": parse_productos(reg.producto),
            "creacion": reg.creacion,
            "total": reg.total
        } for reg in registros_pedidos]

        return db_output


@app.get("/api/v1/pedidos/{id}", tags=["API Endpoints"])
async def pedido_by_id(request: Request, id: str, token: str = Depends(Oauth2_scheme)):
    base_url = request.url.path.rsplit("/", 1)[0]
    oauth.authorization(base_url, token)
    
    with Session(engine) as session:
        pedido = session.exec(select(Pedido).where(Pedido.id == id)).one_or_none()

    if pedido:
        def parse_productos(produc: str) -> List[dict]:
            pattern = re.compile(r"Producto\(producto='(.*?)', cantidad=(.*?)\)")
            return [{"producto": match.group(1), "cantidad": float(match.group(2))}
                    for match in pattern.finditer(produc)]
        return {
            "pedidoId": pedido.id,
            "userId": pedido.userid,
            "producto": parse_productos(pedido.producto),
            "creacion": pedido.creacion,
            "total": pedido.total
        }
    
    raise HTTPException(status_code=404, detail="El pedido no existe")


@app.post("/api/v1/token", response_model=Token, tags=["API Endpoints"])
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user_db, msg = oauth.authentication(form_data.username, form_data.password)
    if user_db is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=msg,
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=oauth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = oauth.create_access_token(user_db, local_timezone, access_token_expires)

    return {"access_token": access_token, "token_type": "Bearer"}


@app.get("/api/v1/costo", tags=["API Endpoints"])
async def read_costo_pedidos(request: Request, token: str = Depends(Oauth2_scheme)):
    oauth.authorization(request.url.path, token)

    with Session(engine) as session:
        registros_pedidos = session.exec(select(Pedido)).all()

        def parse_productos(produc: str) -> List[dict]:
            pattern = re.compile(r"Producto\(producto='(.*?)', cantidad=(.*?)\)")
            return [{"producto": match.group(1), "cantidad": float(match.group(2))}
                    for match in pattern.finditer(produc)]
        
        db_output = [{
            "pedidoId": reg.id,
            "userId": reg.userid,
            "producto": parse_productos(reg.producto),
            "creacion": reg.creacion,
            "total": reg.total,
            "costo": reg.costo
        } for reg in registros_pedidos]

    return db_output
    

@app.post("/api/v1/start-service", tags=["gRPC Process"])
async def start_order_service(request: Request):
    if not os.path.isfile(SCRIPT_PATH):
        raise HTTPException(status_code=404, detail="El archivo order_service.py no existe.")

    try:
        command = f"python3 {SCRIPT_PATH}" if platform.system() != "Windows" else f"python {SCRIPT_PATH}" 
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = process.communicate(timeout=1)
        if stderr:
            return {"output": stdout, "error": stderr}

        return {"output": stdout, "message": "Order Service.py ejecutado en segundo plano on port 50051"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail=f"Error al ejecutar Order Service.py: {e.stderr}")
    except subprocess.TimeoutExpired:
        return {"message": "Order Service.py está en ejecución en segundo plano on port 50051."}