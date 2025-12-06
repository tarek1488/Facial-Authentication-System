from abc import ABC, abstractmethod


class VectorDBInterface(ABC):
    
    @abstractmethod
    def connect(self):
        pass
    
    
    @abstractmethod
    def disconnect(self):
        pass
    
    @abstractmethod
    def get_collection(self, collection_name: str):
        pass
    
    @abstractmethod
    def is_collection_exists(self, collection_name: str):
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str, embedding_size: int):
        pass
    
    @abstractmethod
    def delete_collection(self, collection_name: str):
        pass
    
    @abstractmethod
    def insert_one_record(self, collection_name: str, clieant_image_path: str, vector: list,
                          meta_data: dict = None, record_id: int = None ):
        pass
    
    @abstractmethod
    def insert_many_records(self, collection_name: str, texts: list, vectors:list,
                            meta_datas: list = None, record_ids : list = None, batch_size: int = 50):
        pass
    
    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list, limit:int = 3):
        pass
    
    
    
       