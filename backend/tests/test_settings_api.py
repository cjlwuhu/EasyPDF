from app.core.config import Settings
from app.services.settings import public_settings


def test_public_settings_masks_api_key():
    settings = Settings(api_key="sk-1234567890abcdef", base_url="https://example.com/v1", model_name="test-model")

    result = public_settings(settings)

    assert result["api_key_masked"] == "sk-********cdef"
    assert result["base_url"] == "https://example.com/v1"
    assert result["model_name"] == "test-model"
