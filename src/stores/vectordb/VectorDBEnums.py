from enum import Enum

class VectorDBProviders(Enum):
    QDRANT = "QDRANT"


class VectorDBMetricMethod(Enum):
    COSINE = "cosine"
    DOT = "dot"