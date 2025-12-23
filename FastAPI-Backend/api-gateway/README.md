# API Gateway

This project provides an API Gateway for the Style Classification and Operation Breakdown Similarity services. The API Gateway routes requests to the appropriate backend services and aggregates responses.

## Table of Contents

- [Installation](#installation)
  - [Using Virtual Environment](#using-virtual-environment)
  - [Using Docker](#using-docker)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)

## Installation

### Using Virtual Environment

1. Clone the repository:

   ```sh
   git clone https://github.com/kingslake-dev/style-clasification.git
   cd ./fastAPI-backend/api-gateway
   ```

2. Create a virtual environment and activate it:

   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies:

   ```sh
   pip install -r requirements.txt
   ```

4. Set up the environment variables:

   - Copy the `.env.example` file to `.env`:
     ```sh
     cp .env.example .env
     ```
   - Fill in the required values in the [`.env`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%22file%3A%2F%2F%2FfastAPI-backend%2Fapi-gateway%2F.env%22%7D%5D%2C%22%22%5D "Go to definition") file.

5. Start the application:

   ```sh
   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```

### Using Docker

1. Clone the repository:

   ```sh
   git clone https://github.com/kingslake-dev/style-clasification.git
   cd ./fastAPI-backend/api-gateway
   ```

2. Build and start the Docker containers:

   ```sh
   docker-compose up --build
   ```

3. The application will be available at `http://localhost:8000`.

## Configuration

The application uses environment variables for configuration. These variables are loaded from the [`.env`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%22file%3A%2F%2F%2FfastAPI-backend%2Fapi-gateway%2F.env%22%7D%5D%2C%22%22%5D "Go to definition") file. The following variables need to be set:

- `ENVIRONMENT`: The environment in which the application is running (e.g., development, production).
- [`CLIENT_URL`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%22file%3A%2F%2F%2FfastAPI-backend%2Fapi-gateway%2F.env%22%7D%5D%2C%22%22%5D "Go to definition"): URL of the client application.
- [`IMAGE_SIMILARITY_SERVICE_URL`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%22file%3A%2F%2F%2FfastAPI-backend%2Fapi-gateway%2F.env%22%7D%5D%2C%22%22%5D "Go to definition"): URL of the Image Similarity Service.
- [`OB_SIMILARITY_SERVICE_URL`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%22file%3A%2F%2F%2FfastAPI-backend%2Fapi-gateway%2F.env%22%7D%5D%2C%22%22%5D "Go to definition"): URL of the Operation Breakdown Similarity Service.

## Usage

1. Start the application using one of the installation methods above.
2. Access the API at `http://localhost:8000`.

## API Endpoints

- Access the API docs at `http://localhost:8000/docs`
