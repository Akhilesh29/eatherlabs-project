"""App configuration."""
import tempfile
from pathlib import Path

from pydantic_settings import BaseSettings


def _temp_subdir(name: str) -> Path:
    """Directory under system temp; not saved in project/codebase."""
    return Path(tempfile.gettempdir()) / "document_verification_engine" / name


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = "Document Verification Engine"
    debug: bool = True
    # Use system temp dir so uploads/reports are not saved in codebase
    upload_dir: Path = _temp_subdir("uploads")
    extracted_dir: Path = _temp_subdir("extracted")
    report_dir: Path = _temp_subdir("reports")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def ensure_dirs(settings: Settings) -> None:
    """Create upload/extract/report directories if they don't exist."""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.extracted_dir.mkdir(parents=True, exist_ok=True)
    settings.report_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
ensure_dirs(settings)
