from .db_schemes.client import Client
from .BaseDataModel import BaseDataModel
from .enums.ClientEnum import ClientEnum
from bson.objectid import ObjectId
class ClientDataModel(BaseDataModel):
    def __init__(self, db_client):
        super().__init__(db_client)
        self.collection = db_client[ClientEnum.COLLECTION_CLIENT_NAME.value]

    @classmethod
    async def initialize_client_model(cls, db_client: object):
        instance = cls(db_client)
        await instance.init_collection_with_index()
        return instance
        
    async def init_collection_with_index(self):
        all_collections = await self.db_client.list_collection_names()
        if ClientEnum.COLLECTION_CLIENT_NAME.value not in all_collections:
            self.collection = self.db_client[ClientEnum.COLLECTION_CLIENT_NAME.value]
            indexes = Client.get_indexes()
            for index in indexes:
                await self.collection.create_index(
                    index["key"],
                    name = index["name"],
                    unique = index["unique"]
                )
                
    async def create_client(self, client: Client):
        result = await self.collection.insert_one(client.model_dump(by_alias=True, exclude_unset=False))
        client.id = result.inserted_id
        return client
    
    async def get_client_by_client_id(self, client_id: str):
        record = await self.collection.find_one({
            "client_id": client_id,
        })
        if not record or record is None:
            return None
        
        return Client(**record)
         