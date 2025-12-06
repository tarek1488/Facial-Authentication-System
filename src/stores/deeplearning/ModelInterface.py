from abc import ABC, abstractmethod

class ModelInterface(ABC):
    
    @abstractmethod
    def set_embedding_model(self, model_name: str, vector_size: int, model_path: str):
        pass
    
    @abstractmethod
    def embed_image(self, image_path: str):
        pass