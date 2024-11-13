# IAEW 2024 5K4

## User Guide

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

### OAuth2 Simulation

The authentication is performed using a user database that simulates an Identity Provider (IdP) and the jwt library to encode and decode the JWT (JSON Web Token). The token is created, create_access_token method, based on information from the user database.

Postman can then be used to generate the token and execute the GET request with that token. The endpoint /api/v1/costo returns cost information, which is only accessible if a valid JWT token is provided.

### Run Consummer on localhost

- Python3 consumer.py

### Start HTTP server

- uvicorn main:app --reload
- HTTP server en localhost, port 8000

### Run Application

- <http://localhost:8000/docs>
