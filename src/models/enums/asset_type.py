from enum import Enum

class AssetTypeEnum(str, Enum):
    FILE = "file"
    TEXT = "text"
    LINK = "link"
    JSON = "json"
    MARKDOWN = "markdown"
