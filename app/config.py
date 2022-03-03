"""Configuration."""
from pydantic import BaseSettings, AnyUrl
from typing import Optional


class Settings(BaseSettings):
    """Robokop ARA settings."""
    openapi_server_url: Optional[AnyUrl]
    openapi_server_maturity: str = "development"
    openapi_server_location: str = "RENCI"
    robokop_kg: AnyUrl = "https://automat.renci.org/robokopkg/1.2"
    aragorn_ranker: AnyUrl = "https://aragorn-ranker.renci.org/1.2"
    node_norm: AnyUrl = "https://nodenormalization-sri.renci.org/1.2"

    class Config:
        env_file = ".env"


settings = Settings()
print(settings)
