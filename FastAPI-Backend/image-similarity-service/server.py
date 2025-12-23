import uvicorn
from app import create_app
from config import settings
from app.database.db_connect import init_db

app = create_app()


@app.on_event("startup")
async def connect_db():
    await init_db()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
