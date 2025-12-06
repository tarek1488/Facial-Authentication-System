from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId

class Client(BaseModel):
    id: Optional[ObjectId] = Field(default_factory=ObjectId, alias="_id")
    client_id: str =  Field(..., min_length=1)
    client_name: str =  Field(..., min_length=1)
    client_image_path: str =  Field(..., min_length=1)
    
    @field_validator('client_id')
    def validate_user_id(cls, value):
        if not value.isalnum():
            raise ValueError('client id must be alphanumeric')
        return value
    
    class Config:
        arbitrary_types_allowed = True
        
    @classmethod
    def get_indexes(cls):
        return [{
            "key" : [("client_id", 1)],
            "name": "client_id_index_1",
            "unique": True
        }]
    