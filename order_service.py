import grpc
from concurrent import futures
import order_pb2
import order_pb2_grpc
from main import _create_pedido, ProductoBase, Producto, Estado
from custom_validation import ValidateListToStr

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
            total=None
        )
                
        # Llamar a la función _create_pedido de main.py
        pedido_creado = _create_pedido(pedido_data)

        # Convertir y retornar el pedido en formato gRPC para la respuesta
        order = order_pb2.Order(
            id=pedido_creado.id,
            usuarioId=pedido_creado.userid,
            productos=[
                order_pb2.ProductoPedido(productoId=prod.producto, cantidad=int(prod.cantidad))
                for prod in productos
            ],
            estado=pedido_creado.estado.value,
            fechaCreacion=pedido_creado.creacion.isoformat(),
            total=pedido_creado.total if pedido_creado.total is not None else 0.0
        )
        return order

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    order_pb2_grpc.add_OrderServiceServicer_to_server(OrderService(), server)
    server.add_insecure_port('[::]:50051')  # Puerto del servidor
    print("Servidor gRPC en ejecución en el puerto 50051...")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
