from ..ModelInterface import ModelInterface
from deepface import DeepFace
from models.enums.ResponseSignal import ResponseSignal
from logging import Logger
class DeepFaceProvider(ModelInterface):
    
    def __init__(self: str):
        self.model_name = None
        self.detector_backend = None
        self.logger = Logger(__name__)
    
    def set_embedding_model(self, model_name: str, detector_backend:str):
        self.model_name = model_name
        self.detector_backend = detector_backend
        try:
            model = DeepFace.build_model(model_name =model_name)
            self.logger.info("loading embedding model succeed")
        except:
            self.logger.error("error in loading embedding model")         
        

    def embed_image(self, image_path: str):
        if self.model_name == None or self.detector_backend ==None:
            return None
        
        out = DeepFace.represent(img_path = image_path, model_name= self.model_name,
                                    detector_backend = self.detector_backend, align = True)
        
        if len(out) == 0 or out == None or out[0]["embedding"] == None:
            return None
        
        vector = out[0]["embedding"]
        return vector
        

        
        
    