from enum import Enum

class ResponseSignal(Enum):
    IMAGE_TYPE_NOT_SUPPORTED = "Image type not supported"
    IMAGE_SIZE_EXCEEDED = "ImageE size exceeded"
    IMAGE_IS_VALID = "Image is valid"
    IMAGE_READ_FAIL = "Image read fail"
    IMAGE_PROCESSING_FALIED = "Image processing failed"
    IMAGE_PROCESSING_SUCCEED = "Image processing succeed"
    CLIENT_ADD_FAIL = "Client add fail"
    CLIENT_ADD_SUCCESS = "Client added successfully"
    LOADING_EMBEDDING_MODEL_FAIL = "Loading embedding model fail cheack model name"
    LOADING_EMBEDDING_MODEL_SUCCEED = "Loading embedding model succeed"
    NO_CLIENT_WITH_SUCH_ID = "No client with such id"
    IMAGE_EMBEDDING_FAIL = "Image Embedding Fail"
    IMAGE_ADDED_TO_VECTOR_DB_SUCCESS = "Image added to vector db"
    CAMERA_FRAME_READ_FAIL = "Camera Frame reading fail"