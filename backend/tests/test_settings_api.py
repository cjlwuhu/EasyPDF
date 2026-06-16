from app.core.config import Settings
from app.services.settings import public_settings


def test_public_settings_masks_api_key():
    settings = Settings(api_key="sk-1234567890abcdef", base_url="https://example.com/v1", model_name="test-model")

    result = public_settings(settings)

    assert result["api_key_masked"] == "sk-********cdef"
    assert result["base_url"] == "https://example.com/v1"
    assert result["model_name"] == "test-model"


def test_public_settings_exposes_local_runtime_fields():
    settings = Settings(
        mysql_host="127.0.0.1",
        mysql_port=3307,
        mysql_database="paper_db",
        storage_dir="../storage-test",
        translation_concurrency=3,
        translation_batch_size=9,
    )

    result = public_settings(settings)

    assert result["mysql_host"] == "127.0.0.1"
    assert result["mysql_port"] == 3307
    assert result["mysql_database"] == "paper_db"
    assert result["storage_dir"] == "../storage-test"
    assert result["translation_concurrency"] == 3
    assert result["translation_batch_size"] == 9
