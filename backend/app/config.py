from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    large_file_threshold: int = 500
    large_function_threshold: int = 50
    complexity_threshold: int = 10

    max_upload_size: int = Field(default=52_428_800, description="Max upload size in bytes (50 MB)")
    max_extracted_size: int = Field(
        default=209_715_200, description="Max total extracted size in bytes (200 MB)"
    )
    max_extracted_files: int = Field(default=10_000, description="Max files in extracted archive")
    upload_directory: str = "/tmp/repolens/uploads"

    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    debug: bool = False

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
