import uvicorn
from fastapi import FastAPI
from app import create_app

from app.routes.image import image_router
from app.routes.search import search_router
from app.routes.home import home_router
from app.routes.get_data import get_data_router

app = create_app()

# Include routers
app.include_router(home_router)
app.include_router(image_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(get_data_router, prefix="/api")


if __name__ == "__main__":
	uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
