from pydantic import BaseModel


class PublicSettings(BaseModel):
    api_key_masked: str
    base_url: str
    model_name: str
    mysql_host: str
    mysql_port: int
    mysql_database: str
    storage_dir: str
    translation_concurrency: int
    translation_batch_size: int


class UpdateAISettingsRequest(BaseModel):
    api_key: str = ""
    base_url: str
    model_name: str


class TestAISettingsResponse(BaseModel):
    ok: bool
    message: str
