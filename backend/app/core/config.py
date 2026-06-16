from functools import cached_property
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "EasyPDF"
    app_env: str = "local"
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "easypdf"
    mysql_user: str = "root"
    mysql_password: str = ""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4.1-mini"
    storage_dir: str = "../storage"
    translation_concurrency: int = Field(default=2, ge=1, le=8)
    translation_batch_size: int = Field(default=6, ge=1, le=20)

    @cached_property
    def database_url(self) -> str:
        return URL.create(
            drivername="mysql+pymysql",
            username=self.mysql_user,
            password=self.mysql_password,
            host=self.mysql_host,
            port=self.mysql_port,
            database=self.mysql_database,
            query={"charset": "utf8mb4"},
        ).render_as_string(hide_password=False)

    @property
    def masked_api_key(self) -> str:
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "********"
        return f"{self.api_key[:3]}********{self.api_key[-4:]}"


settings = Settings()
