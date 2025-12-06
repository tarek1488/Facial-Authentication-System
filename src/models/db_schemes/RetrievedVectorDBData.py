from pydantic import BaseModel, Field, field_validator
from typing import Optional



class RetrievedVectorDBdata(BaseModel):
    client_image_path: str
    score: list
    meta_data: Optional[dict]    
    