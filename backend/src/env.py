from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Env settings for the application.
    """
    OPENAI_API_KEY: str
    OPENAI_MAX_TOKENS_MIN: int = Field(200000, gt=0, description = "The per minute rate limit in tokens.")# https://platform.openai.com/settings/organization/limits

    model_config = SettingsConfigDict(
        env_file="env",
        env_file_encoding="utf-8",
    )

settings = Settings()