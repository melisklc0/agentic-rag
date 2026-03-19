from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    # General Application Settings
    PROJECT_NAME: str = "Agentic RAG API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    IS_DEBUG: bool = False

    # LLM and Tracing Settings
    OPENAI_API_KEY: str
    LANGCHAIN_API_KEY: str
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_PROJECT: str = "AGENTIC-RAG"

    # Core API Server Settings
    CORE_API_PORT: int = 8089

    # Vector Database (Qdrant) Settings
    QDRANT_HOST: str = "localhost" 
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "company_documents"
    QDRANT_VECTOR_SIZE: int = 384 #384 genelde all-MiniLM-L6-v2 gibi popüler embedding modellerinin boyutudur
    

    # Environment Variables (.env) Reading Rules
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Reads settings only when called for the first time, then retrieves them
    quickly from memory (cache). Critical for performance.
    """
    return Settings()
