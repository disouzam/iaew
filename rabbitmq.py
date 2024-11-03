import pika
import subprocess

import pika.exceptions

used_queue = 'cola_test'

def publish_message(message, queue_name=used_queue, host='localhost') -> None:
    connection_parameters = pika.ConnectionParameters(host)
    with pika.BlockingConnection(connection_parameters) as connection:
        channel = connection.channel()
        channel.queue_declare(queue=queue_name)
        channel.basic_publish(exchange='', routing_key=queue_name, body=message)

def send_message(msg: str) -> set:
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
