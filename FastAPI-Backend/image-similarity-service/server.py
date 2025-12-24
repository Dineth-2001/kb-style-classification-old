import uvicorn
from app import create_app
from config import settings
from app.database import pg_connect

app = create_app()


@app.on_event("startup")
async def startup_db():
    """Initialize PostgreSQL table on startup"""
    pg_connect.init_table()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
