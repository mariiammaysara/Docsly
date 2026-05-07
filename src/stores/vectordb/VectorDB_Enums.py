from enum import Enum

class VectorDBEnums(Enum):
    """Supported Vector Databases."""
    QDRANT = "QDRANT"
    PGVECTOR = "PGVECTOR"

class DistanceMethodEnums(Enum):
    """Standard Distance Methods for Vector Search."""
    COSINE = "cosine"
    DOT = "dot"
    EUCLIDEAN = "euclidean"

class PgVectorTableSchemeEnums(Enum):
    """Naming convention for PGVector tables/columns."""
    ID = 'id'
    TEXT = 'text'
    VECTOR = 'vector'
    CHUNK_ID = 'chunk_id'
    METADATA = 'metadata'
    _PREFIX = 'pgvector'

class PgVectorDistanceMethodEnums(Enum):
    """Specific Postgres operators for vector distance."""
    COSINE = "vector_cosine_ops"
    DOT = "vector_l2_ops"

class PgVectorIndexTypeEnums(Enum):
    """Available index types for PGVector."""
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"
