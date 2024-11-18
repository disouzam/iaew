from pydantic import AfterValidator, BaseModel
from sqlmodel import Field, SQLModel
import uuid
from custom_validation import ValidateListToStr
from typing import TypeVar, Annotated
from enum import Enum
import datetime
import pytz


# Set Local Time Zone
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


class PedidoPrecioResponse(BaseModel):
    pedidoId: str = Field(default=str(uuid.uuid4()))
    userId: str = Field(default=str(uuid.uuid4()))
    producto: list[Producto]
    creacion: datetime.datetime = Field(default=lambda: datetime.datetime.now(local_timezone))
    total: float
    costo: float
    

class PedidoResponse(BaseModel):
    pedidoId: str = Field(default=str(uuid.uuid4()))
    userId: str = Field(default=str(uuid.uuid4()))
    producto: list[Producto]
    estado: Estado
    creacion: datetime.datetime = Field(default=lambda: datetime.datetime.now(local_timezone))
    total: float