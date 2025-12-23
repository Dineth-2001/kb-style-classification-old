# Style Classification App Services

This project provides APIs for style classification using machine learning models and finding the best matching layout for a given operation breakdown and best matching layout(ob) for given sketch of a garment style. The API Gateway routes requests to the appropriate backend services and aggregates responses.

## Table of Contents

- [Services](#services)
  - [API Gateway](#api-gateway)
  - [Image Similarity Service](#image-similarity-service)
  - [Operation Breakdown Similarity Service](#operation-breakdown-similarity-service)
- [Installation](#installation)
  - [Using Docker](#using-docker)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)

## Services

### API Gateway

The API Gateway routes requests to the appropriate backend services and aggregates responses. It provides endpoints for image classification and operation breakdown similarity.

### Image Similarity Service

The Image Similarity Service provides an API for style classification using machine learning models. Users can upload images and receive style classifications based on pre-trained models.

### Operation Breakdown Similarity Service

The Operation Breakdown Similarity Service provides an API for finding the best matching layout (layout_id) for a given operation breakdown.

## Installation

### Using Docker

1. Clone the repository:

   ```sh
   git clone https://github.com/kingslake-dev/style-clasification.git
   cd ./fastAPI-backend
   ```

2. Build and start the Docker containers:

   ```sh
   docker-compose up --build
   ```

3. The applications will be available at the following URLs:
   - API Gateway: `http://localhost:8000`
   - Image Similarity Service: `http://localhost:5000`
   - Operation Breakdown Similarity Service: `http://localhost:8001`

## Configuration

The application uses environment variables for configuration. These variables are loaded from the `.env` files in each service directory.

The required configuration is mention `README.md` files inside the each service
