from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://querymind:querymind@localhost:5432/querymind"
    database_url_sync: str = "postgresql+psycopg2://querymind:querymind@localhost:5432/querymind"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.0
    openai_max_tokens: int = 1000

    # SQL Config
    sql_dialect: str = "postgresql"
    sql_max_rows: int = 500

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    # App
    app_env: str = "development"
    secret_key: str = "change-me-in-production"


settings = Settings()
