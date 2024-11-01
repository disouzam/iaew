from pydantic import BaseModel, ConfigDict
import uuid
from sqlmodel import Field, SQLModel
import datetime

class Producto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    producto: str = Field(default=uuid.uuid4())
    cantidad: int

class PedidoBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    producto: str
    estado: str = Field(default="CNF") 
    creacion: datetime
    total: float | None = None

class Pedido(PedidoBase, table=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    userid: str = Field(default_factory=lambda: str(uuid.uuid4()))