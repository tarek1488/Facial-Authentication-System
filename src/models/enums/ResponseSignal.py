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
    