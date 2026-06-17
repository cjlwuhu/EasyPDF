from pathlib import Path

from app.core.config import BACKEND_DIR, Settings, settings
from app.services.ai_client import AIClient


def public_settings(current: Settings = settings) -> dict[str, str | int]:
    return {
        "api_key_masked": current.masked_api_key,
        "base_url": current.base_url,
        "model_name": current.model_name,
        "mysql_host": current.mysql_host,
        "mysql_port": current.mysql_port,
        "mysql_database": current.mysql_database,
        "storage_dir": current.storage_dir,
        "translation_concurrency": current.translation_concurrency,
        "translation_batch_size": current.translation_batch_size,
    }


def update_ai_settings(
    api_key: str,
    base_url: str,
    model_name: str,
    current: Settings = settings,
    env_path: Path | None = None,
) -> dict[str, str | int]:
    normalized_base_url = base_url.strip().rstrip("/")
    normalized_model_name = model_name.strip()
    normalized_api_key = api_key.strip()

    if not normalized_base_url:
        raise ValueError("BASE_URL cannot be empty")
    if not normalized_model_name:
        raise ValueError("Model name cannot be empty")

    if normalized_api_key:
        current.api_key = normalized_api_key
    current.base_url = normalized_base_url
    current.model_name = normalized_model_name

    persist_ai_settings(
        env_path or BACKEND_DIR / ".env",
        api_key=current.api_key,
        base_url=current.base_url,
        model_name=current.model_name,
    )
    return public_settings(current)


async def check_ai_connection(
    api_key: str,
    base_url: str,
    model_name: str,
    current: Settings = settings,
    client_class: type[AIClient] = AIClient,
) -> dict[str, bool | str]:
    normalized_base_url = base_url.strip().rstrip("/")
    normalized_model_name = model_name.strip()
    normalized_api_key = api_key.strip() or current.api_key

    if not normalized_api_key:
        raise ValueError("API key cannot be empty")
    if not normalized_base_url:
        raise ValueError("BASE_URL cannot be empty")
    if not normalized_model_name:
        raise ValueError("Model name cannot be empty")

    client = client_class(
        api_key=normalized_api_key,
        base_url=normalized_base_url,
        model=normalized_model_name,
    )
    await client.complete("This is an EasyPDF AI API connection test. Reply with OK.")
    return {"ok": True, "message": "AI connection succeeded."}


def persist_ai_settings(env_path: Path, api_key: str, base_url: str, model_name: str) -> None:
    values = {
        "API_KEY": api_key,
        "BASE_URL": base_url,
        "MODEL_NAME": model_name,
    }
    existing_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    consumed: set[str] = set()
    next_lines: list[str] = []

    for line in existing_lines:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in values:
            next_lines.append(f"{key}={values[key]}")
            consumed.add(key)
        else:
            next_lines.append(line)

    for key, value in values.items():
        if key not in consumed:
            next_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(next_lines) + "\n", encoding="utf-8")
