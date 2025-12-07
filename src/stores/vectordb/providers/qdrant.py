from ..VectorDBInterface import VectorDBInterface
from ..VectorDBEnums import VectorDBMetricMethod
from qdrant_client import QdrantClient, models
from logging import Logger
from models.db_schemes import RetrievedVectorDBdata
import uuid


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
        self.client = QdrantClient(url=self.data_base_url)

    def disconnect(self):
        self.client = None

    def get_collection(self, collection_name: str):
        try:
            return self.client.get_collection(collection_name=collection_name)
        except Exception:
            self.logger.info("No such collection exists")
            return None

    def is_collection_exists(self, collection_name: str):
        return self.client.collection_exists(collection_name=collection_name)

    def create_collection(self, collection_name: str, embedding_size: int):
        if self.is_collection_exists(collection_name):
            self.logger.info(f"Collection {collection_name} already exists")
            return True

        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size,
                distance=self.distance_method
            )
        )
        return True

    def delete_collection(self, collection_name: str):
        if self.is_collection_exists(collection_name):
            return self.client.delete_collection(collection_name=collection_name)

        self.logger.info("No such collection exists to delete")
        return False

    def insert_one_record(self, collection_name: str, vector: list,
                          meta_data: dict = None, record_id: int = None):

        if not self.is_collection_exists(collection_name):
            self.logger.error("Collection does not exist")
            return None

        if record_id is None:
            record_id = str(uuid.uuid4())  # fallback

        point = models.PointStruct(
            id=str(record_id),                   # FIXED
            payload={"metadata": meta_data or {}},
            vector=vector
        )

        try:
            self.client.upload_points(
                collection_name=collection_name,
                points=[point]
            )
        except Exception as e:
            self.logger.error(f"Error while inserting record: {e}")
            return None

        return True

    def search_by_vector(self, collection_name: str, vector: list, limit: int = 1):
        try:
            # Do NOT wrap in [] or anything
            response = self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return None

        points =  response.points
        if not points:
            self.logger.info("No vector match found")
            return None

        
        # Each point here is a ScoredPoint
        results = [
            RetrievedVectorDBdata(
                score=point.score,
                meta_data=point.payload.get("metadata")  # payload is a dict
            )
            for point in points
        ]

        return results


