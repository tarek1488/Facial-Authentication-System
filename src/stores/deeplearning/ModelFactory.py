from .ModelProviderEnum import ModelProviderEnum
from .providers.deepface import DeepFaceProvider

class ModelProviderFactory:
    
    def __init__(self, config: dict):
        self.config = config
    
    def intialize_provider(self, provider_name: str):
        
        if provider_name == ModelProviderEnum.DEEPFACE.value:
            
            provider = DeepFaceProvider()
            return provider
        
        
        return None