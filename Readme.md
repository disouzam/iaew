# FastAPi, Pydantic, RabbitMQ and Oauth2

## Educational Proyect

### FastApi

Automation engineers often find themselves in situations where, to extract information, they need to write APIs to connect with applications that don't have public API schemas. This project, built using the FastAPI framework, is an example of how to build APIs integrating features like validation (Pydantic), authentication (OAuth2), publishing messages to a message broker (RabbitMQ), and running microservices via gRPC.

### Paydantic Validation

To keep the database data consistent, Pydantic is used to validate both the request body before writing to the database and the response model to prevent invalid responses from endpoints.

### Run RabbitMQ container  

RabbitMQ is one of the most well-known message brokers for implementing the Producer/Consumer pattern.

Others include Kafka, Redis, ActiveMQ, Python Message Service, etc.

docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management

- `-d`: Runs the container in detached mode (in the background).
- `--name rabbitmq`: Names the container "rabbitmq" for easy identification.
- `-p 5672:5672`: Exposes RabbitMQ's standard port for the AMQP protocol (messaging port).
- `-p 15672:15672`: Exposes port 15672 for RabbitMQ's web management interface.
- `rabbitmq:management`: Official RabbitMQ image.

### Oauth2 Simulation

The authentication is performed using two dictionaries that simulate an Identity Provider (IdP), Users and API Registration and the jwt library to encode and decode the JWT (JSON Web Token). The token is created, based on information from the user, roles and expiration time.

Postman can then be used to generate the token and execute the GET request with that token. The endpoint /api/v1/costo returns cost information, which is only accessible if a valid JWT token is provided.

### Run Consummer on localhost

- Python3 consumer.py

### Start HTTP server

- uvicorn main:app --reload
- HTTP server en localhost, port 8000

### Start gRPC server

- Ejecuta el endpoint start-order-service
- Se prueba en postman en con la url <http://localhost:50051> e importando el protobuf de protos/order.proto

Si se quiere ejecutar de forma manual:

- python order_service.py
- gRPC server en localhost, port 50051

### Run Application Documentation

- <http://localhost:8000/docs>

### Postman

In order to get Autenticated and Authorized, Postman must be used running Oauth2 Authentication. A collection is also available ready for import.
