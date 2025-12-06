from ..ModelInterface import ModelInterface
import insightface


class InsightFace(ModelInterface):
    
    def __init__(self):
        return
    
    def set_embedding_model(self, model_name: str, vector_size: int, model_path: str):
        self.model_name = model_name
        self.vector_size = vector_size
        self.model_path = model_path 
        
        #self.model =  
        
        pass
    
    
    def embed_image(self, image):
        pass