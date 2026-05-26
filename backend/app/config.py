from pydantic_settings import BaseSettings
from typing import List
import json
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./trading_journal.db"
    SCREENSHOTS_DIR: str = "./screenshots"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"
    
    # DuckDB analytics
    ANALYTICS_DB_PATH: str = "analytics/analytics.duckdb"
    
    # Ollama
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
