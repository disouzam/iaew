# FastAPi, Pydantic, RabbitMQ, gRPC  and Oauth2

![plot](./figura/logo.png)

## Educational Project

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

The authentication is performed on an API endpoint basis using two dictionaries that simulate an Identity Provider (IdP): Users and API Registration, along with the `jwt` library to encode and decode the JWT (JSON Web Token). The token is created based on the user's information, roles, and expiration time.

Postman can then be used to generate the token and execute the requests with the token. The /api/v1/costo endpoint returns cost information, which is only accessible if a valid JWT token is provided.

### Run Consummer on localhost

- Python3 consumer.py

### Start HTTP server

- uvicorn main:app --reload
- HTTP server en localhost, port 8000

### Start gRPC server

Remote Procedure Call (gRPC) is used to execute an insert service into de database.

- Run the `start-service` endpoint:  
- Test it in Postman using the URL `<http://localhost:50051>` by importing the protobuf file from `order.proto`.  

To run it manually:  

- python order_service.py
- The gRPC server will run on localhost, port 50051.  

### Run Application Documentation

- <http://localhost:8000/docs>

### Postman

To authenticate and authorize, Postman must be used with OAuth2 authentication. A ready-to-import collection is also available.
