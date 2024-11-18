import re
import grpc
from concurrent import futures
from sqlmodel import Session
import order_pb2
import order_pb2_grpc
from model import ProductoBase, Producto, Estado, Pedido
from main import engine

# Clase gRPC para implementar el servicio
class OrderService(order_pb2_grpc.OrderServiceServicer):
    def CreateOrder(self, request, context):
        # Construir lista de productos usando ProductoBase y Producto desde `request`
        productos = [
            Producto(producto=prod.productoId, cantidad=prod.cantidad)
            for prod in request.productos
        ]
        
        # Crear el objeto ProductoBase para pasar a _create_pedido
        pedido_data = ProductoBase(
            producto=productos,
            estado=Estado.Confirmado,
            total=5
        )
                
        # Llamar a la función _create_pedido de main.py
        pedido_creado = create_pedido(pedido_data, request.usuarioId)

        # Convertir y retornar el pedido en formato gRPC para la respuesta
        order = order_pb2.Order(
            id=pedido_creado['pedidoId'],
            usuarioId=pedido_creado['userId'],
            productos=[
                order_pb2.ProductoPedido(productoId=prod['producto'], cantidad=int(prod['cantidad']))
                for prod in pedido_creado['producto']
            ],
            estado='CNF',
            fechaCreacion=pedido_creado['creacion'].isoformat(),
            total=pedido_creado['total'] if pedido_creado['total'] is not None else 0.0
        )
        return order
    
def create_pedido(pedido: ProductoBase, user_id: str = None):
    def extrae_productos(producto_string: str):
        pattern = re.compile(r"Producto\(producto='(.*?)', cantidad=(.*?)\)")
        return [
            {"producto": match.group(1), "cantidad": float(match.group(2))}
            for match in pattern.finditer(producto_string)
        ]

    def create_db_output(db_pedido, productos):
        if (user_id): db_pedido.userid = user_id
        db_pedido.total = sum(prod['cantidad'] * db_pedido.costo for prod in productos)
        return {
            "pedidoId": db_pedido.id,
            "userId": db_pedido.userid,
            "producto": productos,
            "creacion": db_pedido.creacion,
            "total": db_pedido.total
        }
    
    with Session(engine) as session:
        db_pedido = Pedido.model_validate(pedido)
        print(db_pedido)
        productos = extrae_productos(db_pedido.producto)
        db_output = create_db_output(db_pedido, productos)
        session.add(db_pedido)
        session.commit()
        session.refresh(db_pedido)
        
        return db_output

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderService(), server)
    server.add_insecure_port('[::]:50051')  # Puerto del servidor
    print("Servidor gRPC en ejecución en el puerto 50051...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
