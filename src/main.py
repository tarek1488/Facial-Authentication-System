from fastapi import FastAPI
from routes import base, user, authenticate
from contextlib import asynccontextmanager
from helpers.config import get_settings
from motor.motor_asyncio import AsyncIOMotorClient
from stores.vectordb.VectorDBFactory import VectorDBFactory
from stores.deeplearning.ModelFactory import ModelProviderFactory
from stores import Firebase
async def lifespan(app: FastAPI):
    # Getting the enviroments settings
    settings = get_settings()
    
    app.mongo_client = AsyncIOMotorClient(settings.MONGO_DB_URL)
    app.mongo_db = app.mongo_client.get_database(settings.MONGO_DB_DATABASE)
    
    # Intialize vector db Factroy
    vector_db_factory =  VectorDBFactory(config=settings)
    
    # Intialize face model factory
    model_factory = ModelProviderFactory(config=settings)
    model_provider_client = model_factory.intialize_provider(settings.EMBEDDING_MODEL_PROVIDER)
    _ = model_provider_client.set_embedding_model(model_name = settings.EMBEDDING_MODEL_NAME,
                                                              detector_backend = settings.DETECTION_BACKEND)
    
    # Retrieve vector db client
    app.vector_db_client = vector_db_factory.intialize_provider(provider_name=settings.VECTORDB_PROVIDER)
    
    # Retrieve face model client
    app.face_model_client =  model_provider_client
    
    
    # connect to vector db client 
    app.vector_db_client.connect()
    
    #connect to firebase 
    app.firebase_client = Firebase(config= settings)
    app.firebase_client.connect()
    
    yield
    # disconnect all connections
    app.vector_db_client.disconnect()
    app.mongo_client.close()

app = FastAPI(lifespan=lifespan)
app.include_router(base.base_router)
app.include_router(user.client_router)
app.include_router(authenticate.authenticate_router)
