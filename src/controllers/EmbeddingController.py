from .BaseController import BaseController
import os

class EmbeddingController(BaseController):
    def __init__(self, vector_db_client, embedding_client):
        super().__init__()
        self.vector_db_client = vector_db_client
        self.embedding_client = embedding_client
        
    def push_image_to_vector_db(self, image_path: list, meta_data:dict):
        collection_name =  self.app_settings.COLLECTION_NAME
        
        return_val =  self.vector_db_client.create_collection(collection_name = collection_name,
                                                              embedding_size = self.app_settings.EMBEDDING_MODEL_SIZE)
        
        if return_val is None:
            return None
        
        vector =  self.embedding_client.embed_image(image_path = image_path)

        return_val = self.vector_db_client.insert_one_record(collection_name = collection_name,
                                                             vector = vector,
                                                             meta_data = meta_data)
        
        if return_val != True:
            return None
        
        return True 
            
        
    
    