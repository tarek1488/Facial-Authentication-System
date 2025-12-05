from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId

class User(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: str =  Field(..., min_length=1)
    user_name: str =  Field(..., min_length=1)
    
    @field_validator('user_id')
    def validate_user_id(cls, value):
        if not value.isalnum():
            raise ValueError('user id must be alphanumeric')
        return value
    
    class Config:
        arbitrary_types_allowed = True
        
    @classmethod
    def get_indexes(cls):
        return [{
            "key" : [("user_id", 1)],
            "name": "user_id_index_1",
            "unique": True
        }]
    