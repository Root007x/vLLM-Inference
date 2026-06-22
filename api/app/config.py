from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODEL: str
    API_KEY: str
    VLLM_URL: str = "http://vllm:8000/v1"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
