from .BaseController import BaseController
from fastapi import UploadFile
from models.enums.ResponseSignal import ResponseSignal
import re
from .ClientController import ClientController
import os
import cv2
import numpy as np
class ImageController(BaseController):
    def __init__(self):
        super().__init__()
        
    def validate_image(self, file: UploadFile):
        if file.content_type not in self.app_settings.IMAGE_ALLOWED_EXTENSIONS:
            return False, ResponseSignal.IMAGE_TYPE_NOT_SUPPORTED.value
        
        return True, ResponseSignal.IMAGE_IS_VALID.value
    
    def generate_unique_file_path(self, original_file_name:str, client_id: str):
        
        random_file_name = self.generate_random_string()
        
        client_diectory = ClientController().get_client_path(client_id=client_id)
        
        clean_file_name = self.clean_file_name(file_name= original_file_name)
        
        
        
        new_unique_file_path = os.path.join(client_diectory, random_file_name + "_" + clean_file_name)
        
        
        while os.path.exists(new_unique_file_path):
            random_file_name = self.generate_unique_file_name
            new_unique_file_path = os.path.join(clean_file_name, random_file_name + "_" + clean_file_name)
        
        return new_unique_file_path, random_file_name + "_" + clean_file_name
        
        
    def clean_file_name(self, file_name: str):
                    
        cleaned_name = re.sub(r'[^\w_.]', '', file_name.strip())
        
        cleaned_name = cleaned_name.replace(" ", "_") 
        
        return cleaned_name   
    
    def read_frame(self, file: UploadFile):
        file_bytes = np.frombuffer(file.file.read(), np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        if img is None:
            return None
        
        return img 