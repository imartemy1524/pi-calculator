# Pi Calculation API

This is a simple Flask application that calculates Pi to a given number of digits using a Celery worker.

## Getting Started

To get the application running, follow these steps:

1.  **Build the Docker containers:**
    ```bash
    docker-compose build
    ```

2.  **Start the application:**
    ```bash
    docker-compose up
    ```

The Flask application will be available at `http://localhost:5000`.

## API Documentation

The API is documented using Swagger. You can access the interactive Swagger UI here:

[http://localhost:5000/apidocs](http://localhost:5000/apidocs)
