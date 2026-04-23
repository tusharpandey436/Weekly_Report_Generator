"""
Application configuration using Pydantic BaseSettings.
Values are read from environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Weekly Data Analyst"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    ENABLE_GEMINI: bool = False
    MAX_FILE_SIZE_MB: int = 10
    DATE_COLUMN_NAME: str = "Date"
    DESCRIPTION_COLUMN_NAME: str = "Description"
    DESCRIPTION_BULLET_LIMIT: int = 15
    DESCRIPTION_LOG_LIMIT: int = 50

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
