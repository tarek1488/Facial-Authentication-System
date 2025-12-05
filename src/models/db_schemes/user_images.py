from pydantic import BaseModel, Field, field_validator
from typing import Optional
from bson.objectid import ObjectId

class UserImage(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    image_path:str =  Field(..., min_length=1)
    image_user_id : ObjectId
    
    
    class Config:
        arbitrary_types_allowed = True
    
    @classmethod
    def get_indexes(cls):
        return [{
            "key" : [("image_user_id", 1)],
            "name": "image_user_id_index_1",
            "unique": False
        }]