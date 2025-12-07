from pydantic import BaseModel, Field, field_validator
from typing import Optional



class RetrievedVectorDBdata(BaseModel):
    score: float
    meta_data: Optional[dict]    
    