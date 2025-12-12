import firebase_admin
from firebase_admin import db, credentials
from firebase_admin import delete_app
from logging import Logger
class Firebase:
    def __init__(self, config):
        self.config = config
        self.app = None
        self.logger  = Logger(__name__)
        
    def connect(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate(self.config.CREDENTIALS_PATH)
            self.app = firebase_admin.initialize_app(
                cred,
                {"databaseURL": self.config.DATABASE_URL}
            )
        else:
            self.app = firebase_admin.get_app()
            
    def disconnect(self):
        delete_app(self.app)
    
    def update_value(self, value: bool):
        try:
            db.reference("/").update({"Status": value})
            self.logger.info("Data updated successfully in Firebase")
            return True
        except Exception as e:
            self.logger.error("Error in updatin firebase")
            return False
            
