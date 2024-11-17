
# RabbitMQ Producer
# By Ed Scrimaglia

import pika
import pika.exceptions

used_queue = 'cola_test'

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


def publish_message(message, queue_name=used_queue, host='localhost') -> None:
    connection_parameters = pika.ConnectionParameters(host)
    with pika.BlockingConnection(connection_parameters) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)


def send_message(msg: str) -> tuple[bool,str]:
    status = False
    try:
        publish_message(msg)
        status = True
        err = "No error"
    except pika.exceptions.AMQPConnectionError:
        err = "RabbitMQ connection error"
    except pika.exceptions.AMQPChannelError as err:
        err =  f"RabbitMQ queue {used_queue} can not be used"
    
    return (status,err)
