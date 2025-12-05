from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    
    
    
    VECTORDB_PROVIDER: str = None
    VECTORDB_PATH: str = None
    VECTORDB_DISTANCE_METHOD: str = None
    QDRANT_URL:str = None
    
    
    class Config:
        env_file = ".env"
        
def get_settings():
    return Settings()    