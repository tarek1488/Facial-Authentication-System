from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import VectorDBMetricMethod
from qdrant_client import QdrantClient, models
from logging import Logger
from models.db_schemes import RetrievedVectorDBdata
class Qdrant(VectorDBInterface):
    
    def __init__(self, data_base_url, distance_method):
        if distance_method == VectorDBMetricMethod.COSINE.value:
            self.distance_method = models.Distance.COSINE
        
        elif distance_method == VectorDBMetricMethod.DOT.value:
            self.distance_method = models.Distance.DOT
            
        self.data_base_url = data_base_url
        
        self.client = None
        
        self.logger = Logger(__name__)
    
    def connect(self):
        self.client =  QdrantClient(url = self.data_base_url)
    
    def disconnect(self):
        self.client = None
        
    
    
    def get_collection(self, collection_name: str):
        collection = self.client.get_collection(collection_name= collection_name)
        
        if collection or collection is not None:
            return collection
        
        self.logger.info("no such a collection exists")
        
    
    def is_collection_exists(self, collection_name: str):
        return self.client.collection_exists(collection_name= collection_name)
    
    
    def create_collection(self, collection_name: str, embedding_size: int):
        collection_status = self.is_collection_exists(collection_name=collection_name)
        
        if collection_name:
            self.logger.info(f"there is a collection with name {collection_name} already exists")
            return None
        
        _ = self.client.create_collection(collection_name= collection_name,
                                          vectors_config= models.VectorParams(size= embedding_size, distance=self.distance_method))
        
        return True
        
        
    
    
    def delete_collection(self, collection_name: str):
        
        if self.is_Collection_exists(collection_name= collection_name):
            return self.client.delete_collection(collection_name= collection_name)
        
        self.logger.info("There no such a collection exists with this name to be deleted")
        
    
    
    def insert_one_record(self, collection_name: str, vector: list,
                          meta_data: dict = None, record_id: int = None ):
        
        #check if collection exits or not
        if not self.is_Collection_exists(collection_name= collection_name):
            self.logger.error("There is no such a collection exits with this name")
            return None
        
        point =  models.PointStruct(
            id= [record_id],
            payload= {"metadata": meta_data},
            vector= vector
        )
        try:
            _ = self.client.upload_points(collection_name= collection_name,points=[point],)
        
        except Exception as e:
                self.logger.error(f"Error while inserting one record: {e}")
        
        return True
    
    
    
    def search_by_vector(self, collection_name: str, vector: list, limit:int = 3):
        documents = self.client.search(collection_name= collection_name,
                                  query_vector= vector,
                                  limit=limit)
        
        if not documents or len(documents) == 0:
            self.logger.info("No such a cleint vector returend")
            return None
        
        
        
        data = [RetrievedVectorDBdata(client_image_path=doc.payload["client_image_path"],
                                      score=doc.score,
                                      meta_data=doc.payload["metadata"])
                for doc in documents]
        
        return data
        