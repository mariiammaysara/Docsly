from enum import Enum

class ProcessingStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingEnum(str, Enum):
    TXT = ".txt"
    PDF = ".pdf"
