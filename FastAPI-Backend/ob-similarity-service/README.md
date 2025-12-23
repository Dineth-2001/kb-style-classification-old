# Operation Breakdown Similarity Service

This project provides an API for finding the best matching layout (layout_id) for a given operation breakdown.

## Table of Contents

- [Installation](#installation)
  - [Using Virtual Environment](#using-virtual-environment)
  - [Using Docker](#using-docker)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Developers](#developers)

## Installation

### Using Virtual Environment

1. Clone the repository:

   ```sh
   git clone https://github.com/kingslake-dev/style-clasification.git
   cd ./fastAPI-backend/ob-similarity-service
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

5. Start the application:

   ```sh
   uvicorn server:app --host 0.0.0.0 --port 5000 --reload
   ```

### Using Docker

1. Clone the repository:

   ```sh
   git clone https://github.com/kingslake-dev/style-clasification.git
   cd ./fastAPI-backend/ob-similarity-service
   ```

2. Build and start the Docker containers:

   ```sh
   docker-compose up --build
   ```

3. The application will be available at `http://localhost:5000`.

## Configuration

The application uses environment variables for configuration. These variables are loaded from the `.env` file. The required variables are:

- `ENVIRONMENT`
- `CLIENT_URL`
- `DATABASE_URL`

## Usage

1. Start the application using one of the installation methods above.
2. Access the API at `http://localhost:5000`.

## API Endpoints

- Access the API docs at `http://localhost:5000/docs`
