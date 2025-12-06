from .providers import Qdrant
from .VectorDBEnums import VectorDBProviders
from controllers.BaseController import BaseController
class VectorDBFactory:
    
    def __init__(self, config: dict):
        self.config = config
        self.base_controller = BaseController()
        
    def intialize_provider(self, provider_name: str):
        
        if provider_name == VectorDBProviders.QDRANT.value:
            
            provider = Qdrant(data_base_url= self.config.QDRANT_URL, 
                                      distance_method= self.config.VECTORDB_DISTANCE_METHOD)
            return provider
        return None
            
    
    