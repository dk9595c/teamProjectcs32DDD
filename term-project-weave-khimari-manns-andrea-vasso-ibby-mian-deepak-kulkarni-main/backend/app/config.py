from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # API
    api_prefix: str = "/api/v1"
    
    # Data
    data_dir: str = "data"
    snapshots_dir: str = "data/snapshots/demo"
    
    # Financial Data Provider (for future integration)
    financial_data_provider: Optional[str] = None
    polygon_api_key: Optional[str] = None
    alpha_vantage_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()