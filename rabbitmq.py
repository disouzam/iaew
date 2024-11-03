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

def callback(ch, method, properties, body) -> str:
    return f" [x] Received {body.decode()}"

def consume_messages():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        channel.queue_declare(queue=used_queue)

        channel.basic_consume(queue=used_queue, on_message_callback=callback, auto_ack=True)

        print(' [*] Leyendo cola en RabbitMQ. To exit press CTRL+C')
        
        channel.start_consuming()
    except pika.exceptions.AMQPConnectionError as err:
        print ("RabbitMQ connection error")
    except pika.exceptions.AMQPChannelError as err:
        print (f"RabbitMQ queue {used_queue} can not be used")
    except (Exception, KeyboardInterrupt) as err:
        print (err)

def read_message():
    consume_messages()