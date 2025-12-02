from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "openai:gpt-4o"
    LOGFIRE_SERVICE_NAME: str = "rfp-agentic"
    LOGFIRE_SEND_TO_LOGFIRE: bool = True
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    JWT_SECRET: str = "change_me"
    JWT_ALGORITHM: str = "HS256"
    API_URL: str = "http://localhost:8000/api"

    class Config:
        env_file = ".env"


settings = Settings()
