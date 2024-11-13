
import datetime
import os
import platform
import subprocess
import uuid
from pydantic import AfterValidator, BaseModel
from fastapi import FastAPI, HTTPException, Depends, status
from sqlmodel import Field, SQLModel, create_engine, Session, select
import rabbitmq as rb
from oauth2 import User, DataBase, Token, Autenticator
import json
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
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

app = FastAPI(title="IAEW", description="REST Full API TP - Grupo 1 - 2024", version="1.0.0")

# Dependencia para el esquema de autenticación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Objetos de SQLite y el ORM
sqlite_file_name = "iaew.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)

# Body to publish by publisher
for_publishing = {
        'pedidoId': '880e8400-e29b-41d4-a716-446655440000',
        'userId': '550e8400-e29b-41d4-a716-446655440000',
        'producto': [
            {
            'producto': '770e8400-e29b-41d4-a716-446655440000',
            'cantidad': 2
            }
        ],
        'creacion': '2023-10-01T16:00:00Z'
    }

# Rutas
@app.post("/api/v1/pedido", tags=["Métodos principales"])
def create_pedido(pedido: ProductoBase):
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


@app.post("/api/v1/producer",tags=["Métodos principales"])
def publish_pedido():
    try:
        msg = json.dumps(for_publishing, indent=2)
        result = rb.send_message(msg=msg)
        success, response_message = result
        print (success, response_message)
        if not success:
            msg = {"RabbitMQ": response_message}
        else:
            msg = for_publishing
        return msg
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error al decodificar formato JSON")
    except TypeError as err:
        raise HTTPException(status_code=422, detail="Error de tipo: " + str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail="Error: " + str(err))
    

@app.get("/api/v1/pedidos", response_model=list[PedidoResponse], tags=["Métodos principales"])
def read_pedidos() -> List[dict]:
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


@app.get("/api/v1/pedido/{id}", tags=["Métodos principales"])
async def pedido_by_id(id: str):
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


@app.post("/api/v1/token", response_model=Token, tags=["Métodos principales"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = Autenticator.authentication(DataBase.users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = datetime.timedelta(minutes=Autenticator.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = Autenticator.create_access_token({"sub": user['username']}, local_timezone, access_token_expires)
    return {"access_token": access_token, "token_type": "Bearer"}


@app.get("/api/v1/costo", tags=["Sólo Documentación (usar Postman con Auth2.0)"])
async def read_costo_pedidos(token: str = Depends(oauth2_scheme)):
    def raise_credentials_exception(detail: str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, Autenticator.SECRET_KEY, algorithms=[Autenticator.ALGORITHM])
        username: str = payload.get("sub")
        
        if not username:
            raise_credentials_exception("Could not validate credentials")
        
        user = Autenticator.authentication(DataBase.users_db, username)
        token_data = User(username=username)
    except (jwt.PyJWTError, jwt.ExpiredSignatureError) as error:
        raise_credentials_exception("Could not validate credentials")

    user = DataBase.users_db.get(token_data.username)
    
    if not user:
        raise_credentials_exception("Could not validate credentials")

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

@app.post("/start-order-service", tags=["Procesos"])
async def start_order_service():
    # Verifica si el archivo existe
    if not os.path.isfile(SCRIPT_PATH):
        raise HTTPException(status_code=404, detail="El archivo order_service.py no existe.")

    # Chequea si el proceso ya está en ejecución
    # if is_process_running("order_service.py"):
    #     return {"message": "Ya hay una instancia de order_service.py en ejecución."}

    try:
        # Usa 'python3' en lugar de 'python' para compatibilidad con Linux
        command = f"python3 {SCRIPT_PATH}" if platform.system() != "Windows" else f"python {SCRIPT_PATH}"
        
        # Ejecuta el script en segundo plano usando Popen
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Captura de salida inicial sin bloquear
        stdout, stderr = process.communicate(timeout=1)

        # Retorna el estado de ejecución
        if stderr:
            return {"output": stdout, "error": stderr}

        return {"output": stdout, "message": "order_service.py ejecutado en segundo plano"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail=f"Error al ejecutar order_service.py: {e.stderr}")
    except subprocess.TimeoutExpired:
        return {"message": "order_service.py está en ejecución en segundo plano."}