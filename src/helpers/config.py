from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    
    IMAGE_ALLOWED_EXTENSIONS: list
    IMAGE_CHUNK_SIZE: int
    
    MONGO_DB_URL: str
    MONGO_DB_DATABASE: str
    
    EMBEDDING_MODEL_PROVIDER: str
    EMBEDDING_MODEL_NAME: str
    EMBEDDING_MODEL_SIZE: int
    DETECTION_BACKEND: str
    DEEPFACE_HOME: str
    
    VECTORDB_PROVIDER: str = None
    VECTORDB_PATH: str = None
    VECTORDB_DISTANCE_METHOD: str = None
    QDRANT_URL:str = None
    COLLECTION_NAME: str = None
    
    class Config:
        env_file = ".env"
        
def get_settings():
    return Settings()    