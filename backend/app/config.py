from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    large_file_threshold: int = 500
    large_function_threshold: int = 50
    complexity_threshold: int = 10

    max_upload_size: int = Field(default=26_214_400, description="Max upload size in bytes (25 MB)")
    max_extracted_size: int = Field(
        default=104_857_600, description="Max total extracted size in bytes (100 MB)"
    )
    max_extracted_files: int = Field(default=5_000, description="Max files in extracted archive")
    max_single_file_size: int = Field(
        default=10_485_760, description="Max single extracted file size in bytes (10 MB)"
    )
    max_analysis_seconds: int = Field(default=60, description="Max analysis runtime in seconds")
    gemini_top_findings_limit: int = Field(default=15, description="Max findings sent to Gemini")
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
