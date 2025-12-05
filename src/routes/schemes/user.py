from pydantic_settings import BaseSettings
from typing import Optional

class UserRequest(BaseSettings):
    USER_NAME : Optional[str] = None
    USER_ID: Optional[int]= 100

    