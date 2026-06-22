from __future__ import annotations

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: PostgresDsn
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "BAAI/bge-reranker-base"

    pool_min_size: int = 4
    pool_max_size: int = 20
    hnsw_ef_search: int = 40

    embed_batch_size: int = 64
    rerank_batch_size: int = 16

    rrf_k: int = 60
    fusion_top_k: int = 30
