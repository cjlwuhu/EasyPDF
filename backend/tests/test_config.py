from app.core.config import Settings


def test_database_url_uses_mysql_settings():
    settings = Settings(
        mysql_host="localhost",
        mysql_port=3306,
        mysql_database="easypdf",
        mysql_user="root",
        mysql_password="secret",
    )

    assert settings.database_url == "mysql+pymysql://root:secret@localhost:3306/easypdf?charset=utf8mb4"


def test_database_url_escapes_mysql_password():
    settings = Settings(mysql_password="p@ss:word/with#chars")

    assert "p%40ss%3Aword%2Fwith%23chars" in settings.database_url


def test_api_key_is_masked():
    settings = Settings(api_key="sk-1234567890abcdef")

    assert settings.masked_api_key == "sk-********cdef"
