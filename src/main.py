from fastapi import FastAPI
from routes import base
from contextlib import asynccontextmanager
from helpers.config import get_settings

async def lifespan(app: FastAPI):
    # Getting the enviroments settings
    settings = get_settings()
    
    yield
    app.vector_db_client.disconnect()
    app.mongo_client.close()

app = FastAPI(lifespan=lifespan)
app.include_router(base.base_router)
