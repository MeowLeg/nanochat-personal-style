from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    openai_api_key: str
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: str = "./data"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()