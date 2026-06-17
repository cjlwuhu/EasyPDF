from app.core.config import Settings
from app.services.settings import public_settings, update_ai_settings


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


def test_update_ai_settings_changes_runtime_values_without_echoing_secret(tmp_path):
    settings = Settings(api_key="", base_url="https://old.example/v1", model_name="old-model")
    env_path = tmp_path / ".env"

    result = update_ai_settings(
        api_key="sk-test-secret",
        base_url="https://new.example/v1",
        model_name="new-model",
        current=settings,
        env_path=env_path,
    )

    assert settings.api_key == "sk-test-secret"
    assert settings.base_url == "https://new.example/v1"
    assert settings.model_name == "new-model"
    assert result["api_key_masked"] == "sk-********cret"
    assert "sk-test-secret" not in str(result)


def test_update_ai_settings_keeps_existing_key_when_blank(tmp_path):
    settings = Settings(api_key="sk-existing-secret", base_url="https://old.example/v1", model_name="old-model")

    update_ai_settings(
        api_key="",
        base_url="https://new.example/v1",
        model_name="new-model",
        current=settings,
        env_path=tmp_path / ".env",
    )

    assert settings.api_key == "sk-existing-secret"
    assert settings.base_url == "https://new.example/v1"
    assert settings.model_name == "new-model"
