import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # AWS
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID: str = os.getenv(
        "BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"
    )
    BEDROCK_EMBEDDING_MODEL_ID: str = os.getenv(
        "BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0"
    )

    # Document Processing
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    MAX_CHUNKS_PER_QUERY: int = int(os.getenv("MAX_CHUNKS_PER_QUERY", "5"))

    # FAISS
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "./storage/faiss_index")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Paths
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")


config = Config()
