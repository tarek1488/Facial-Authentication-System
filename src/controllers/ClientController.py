from .BaseController import BaseController
import os


class ClientController(BaseController):
    def __init__(self):
        super().__init__()
    
    def get_client_path(self, client_id: str):
        
        client_directory = os.path.join(self.files_dir, client_id)
        
        if not os.path.exists(client_directory):
            os.makedirs(client_directory)
        
        return client_directory
        