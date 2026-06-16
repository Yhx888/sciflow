from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    zotero_api_key: str = ""
    zotero_user_id: str = ""
    lark_doc_template: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


def get_settings() -> Settings:
    return Settings()


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    return get_project_root() / "data"


def get_output_dir() -> Path:
    return get_project_root() / "output"


def ensure_directories():
    get_data_dir().mkdir(exist_ok=True)
    get_output_dir().mkdir(exist_ok=True)
