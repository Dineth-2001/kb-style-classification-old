# Style Classification API

This project provides an API for style classification using machine learning models. The API allows users to upload images and receive style classifications based on pre-trained models.

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
   cd ./fastAPI-backend/image-classification-service
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
   - Fill in the required values in the [`.env`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2Fdocker-compose.dev.yml%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A13%2C%22character%22%3A8%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition") file.

5. Start the application:

   ```sh
   uvicorn server:app --host 0.0.0.0 --port 5000 --reload
   ```

### Using Docker

1. Clone the repository:

   ```sh
   git clone https://github.com/kingslake-dev/style-clasification.git
   cd ./fastAPI-backend/image-classification-service
   ```

2. Build and start the Docker containers:

   ```sh
   docker-compose up --build
   ```

3. The application will be available at `http://localhost:5000`.

## Configuration

The application uses environment variables for configuration. These variables are loaded from the [`.env`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2Fdocker-compose.dev.yml%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A13%2C%22character%22%3A8%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition") file. The following variables need to be set:

- `ENVIRONMENT`: The environment in which the application is running (e.g., development, production).
- [`MONGO_URL`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A1%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env.example%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A1%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2Ftest.md%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A46%2C%22character%22%3A4%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition"): MongoDB connection URL.
- [`MONGO_DB`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A2%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env.example%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A2%2C%22character%22%3A0%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition"): MongoDB database name.
- [`CLIENT_URL`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A3%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env.example%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A3%2C%22character%22%3A0%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition"): URL of the client application.
- [`AWS_ACCESS_KEY`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A4%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env.example%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A4%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2Ftest.md%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A49%2C%22character%22%3A4%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition"): AWS access key for S3.
- [`AWS_SECRET_ACCESS_KEY`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A5%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env.example%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A5%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2Ftest.md%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A50%2C%22character%22%3A4%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition"): AWS secret access key for S3.
- [`AWS_REGION`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A6%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env.example%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A6%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2Ftest.md%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A51%2C%22character%22%3A4%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition"): AWS region for S3.
- [`AWS_BUCKET_NAME`](command:_github.copilot.openSymbolFromReferences?%5B%22%22%2C%5B%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A7%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2F.env.example%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A7%2C%22character%22%3A0%7D%7D%2C%7B%22uri%22%3A%7B%22scheme%22%3A%22file%22%2C%22authority%22%3A%22%22%2C%22path%22%3A%22%2Fd%3A%2FKingslake%2Fstyle-classification%2Ffast_api%2Ftest.md%22%2C%22query%22%3A%22%22%2C%22fragment%22%3A%22%22%7D%2C%22pos%22%3A%7B%22line%22%3A52%2C%22character%22%3A4%7D%7D%5D%2C%229bb9dd1a-e1cb-4998-a26b-9de1e7414738%22%5D "Go to definition"): AWS S3 bucket name.

## Usage

1. Start the application using one of the installation methods above.
2. Access the API at `http://localhost:5000`.

Recommended quick steps:

- Install Python deps (ensure `torch` and `transformers` are available):

```bash
python -m pip install -r requirements.txt
```

- Populate the vector DB from S3 (example):

```bash
# from repository root
cd image-similarity-service
# scan whole bucket (uses env AWS_* + MONGO_* vars from .env)
python create_embeddings_s3.py --prefix "" --dry-run   # dry-run first
python create_embeddings_s3.py --prefix ""              # run for real
```

## API Endpoints & Examples

All endpoints are prefixed with `/img` in this service.

- Save an uploaded image (uploads to S3, computes CLIP embedding, stores in DB):

```bash
curl -X POST "http://localhost:5000/img/save-image" \
   -F "image=@/path/to/image.jpg" \
   -F "layout_code=layout123" \
   -F "style_type=dress" \
   -F "tenant_id=tenant_abc"
```

- Update an existing image (replaces S3 object and embedding):

```bash
curl -X PUT "http://localhost:5000/img/update-image" \
   -F "image=@/path/to/new-image.jpg" \
   -F "layout_code=layout123" \
   -F "style_type=dress" \
   -F "tenant_id=tenant_abc"
```

- Search by uploading a query image (computes CLIP embedding and returns top-K similar images):

```bash
curl -X POST "http://localhost:5000/img/search-image" \
   -F "image=@/path/to/query.jpg" \
   -F "style_type=dress" \
   -F "no_of_results=10"
```

Response (JSON) will contain top matches with keys: `tenant_id`, `image_url`, `similarity_score`, and `rank`.

Notes
- Embeddings: CLIP (openai/clip-vit-large-patch14) with `image_size=224` is used for all embeddings.
- No additional preprocessing is performed before embedding — raw image bytes are passed to CLIP.
- Ensure environment variables in `.env` are set (AWS credentials, MongoDB URL, bucket name, etc.).
- If your stored vectors were generated with a different model, re-run `create_embeddings_s3.py` to regenerate CLIP vectors.

-- Access the API docs at `http://localhost:5000/docs`
