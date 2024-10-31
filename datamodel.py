from pydantic import BaseModel, ConfigDict
import uuid
from sqlmodel import Field, SQLModel, create_engine, Session, select
import datetime

#try:
class Producto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True) 
    producto: str = Field(default=uuid.uuid4)
    cantidad: int

class PedidoBase(SQLModel):
    model_config = ConfigDict(arbitrary_types_allowed=True) 
    userid: str = Field(default=uuid.uuid4)
    productos: str
    estado: str = Field(default="CNF") 
    fechacreacion: datetime
    total: float | None = None

class Pedido(PedidoBase, table=True):
    id: str = Field(default=uuid.uuid4, primary_key=True)
# except PydanticUserError as exc_info:
#     assert exc_info.code == 'schema-for-unknown-type'