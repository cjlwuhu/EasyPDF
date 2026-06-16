from app.core.config import Settings, settings


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
