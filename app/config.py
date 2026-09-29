from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================
    # API Keys
    # =========================
    google_api_key: str

    # =========================
    # Models
    # =========================
    llm_model: str
    embedding_model: str
    reranker_model: str
    tavily_api_key : str
    # Retrieval
    retrieval_top_k: int
    rerank_top_k: int
    
    # =========================
    # Chunking
    # =========================

    unit_threshold: int
    chunk_size: int
    chunk_overlap: int

    # =========================
    # Paths
    # =========================
    vector_store_path: str
    raw_data_path: str
    processed_data_path: str
    upload_path: str

    # =========================
    # Logging
    # =========================
    log_level: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()