import firebase_admin
from firebase_admin import db, credentials

class Firebase():
    def __init__(self, config: dict):
        self.config = config
        self.cred = credentials("")
        pass
    