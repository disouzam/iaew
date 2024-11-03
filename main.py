
from datetime import datetime
import uuid
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from sqlmodel import Field, SQLModel, create_engine, Session, select
import rabbitmq as rb
import json

class Producto(BaseModel):
    producto: str = Field(default=uuid.uuid4())
    cantidad: int

class PedidoBase(SQLModel):
    producto: str
    estado: str = Field(default="CNF") 
    creacion: datetime
    total: float | None = None

class Pedido(PedidoBase, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    userid: str = Field(default_factory=lambda: str(uuid.uuid4()))

sqlite_file_name = "iaew.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

SQLModel.metadata.create_all(engine)

app = FastAPI()


@app.post("/api/v1/pedido")
def create_pedido(pedido: PedidoBase):
    with Session(engine) as session:
        db_pedido = Pedido.model_validate(pedido)
        session.add(db_pedido)
        session.commit()
        session.refresh(db_pedido)
        return db_pedido
    
@app.post("/api/v1/producer")
def publish_pedido(body: str):
    try:
        msg = json.loads(body)
        result = rb.send_message(msg=body)
        if not bool(result[0]):
            msg = {"RabbitMQ": result[1]}
        return msg
    except json.JSONDecodeError:
        return  {"error": "Error al decodificar formato JSON"}
    except Exception as err:
        return {"error: ",str (err)}
    
@app.get("/api/v1/pedidos")
def read_pedidos():
    with Session(engine) as session:
        pedidos = session.exec(select(Pedido)).all()
        return pedidos

@app.get("/api/v1/pedidos/{id}")
async def pedidos_by_id(id: str):
    with Session(engine) as session:
        pedidos = session.exec(select(Pedido)).all()
    
    for pedido in pedidos:
        if pedido.id == id:
            return pedido
    raise HTTPException(status_code=404, detail="El pedido no existe")