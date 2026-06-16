from app.core.config import Settings, settings


def public_settings(current: Settings = settings) -> dict[str, str]:
    return {
        "api_key_masked": current.masked_api_key,
        "base_url": current.base_url,
        "model_name": current.model_name,
    }
