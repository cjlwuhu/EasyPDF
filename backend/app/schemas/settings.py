from pydantic import BaseModel


class PublicSettings(BaseModel):
    api_key_masked: str
    base_url: str
    model_name: str
