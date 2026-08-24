from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LLM_API_URL: str = "https://api.openai.com/v1/chat/completions"
    LLM_API_KEY: str = "sk-placeholder"
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    CORS_ORIGINS: str = "http://localhost,http://localhost:80"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
