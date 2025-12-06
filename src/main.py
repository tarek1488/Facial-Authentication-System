from fastapi import FastAPI
from routes import base, user
from contextlib import asynccontextmanager
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
from stores.vectordb.VectorDBFactory import VectorDBFactory
async def lifespan(app: FastAPI):
    # Getting the enviroments settings
    settings = get_settings()
    
    app.mongo_client = AsyncIOMotorClient(settings.MONGO_DB_URL)
    app.mongo_db = app.mongo_client.get_database(settings.MONGO_DB_DATABASE)
    
    # Intialize Factroy
    vector_db_factory =  VectorDBFactory(config=settings)
    
    # Retrieve vector db client
    app.vector_db_client = vector_db_factory.intialize_provider(provider_name=settings.VECTORDB_PROVIDER)
    
    # connect to vector db client 
    app.vector_db_client.connect()
    
    yield
    # disconnect all connections
    app.vector_db_client.disconnect()
    app.mongo_client.close()

app = FastAPI(lifespan=lifespan)
app.include_router(base.base_router)
app.include_router(user.client_router)
