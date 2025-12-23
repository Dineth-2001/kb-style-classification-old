from app import create_app
from config import settings
import uvicorn

from app.routes.save import save_router
from app.routes.search import search_router
from app.routes.get_data import data_router
from app.routes.status import status_router

app = create_app()

# Routes
app.include_router(status_router)
app.include_router(save_router, prefix="/ob")
app.include_router(search_router, prefix="/ob")
app.include_router(data_router, prefix="/ob")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
