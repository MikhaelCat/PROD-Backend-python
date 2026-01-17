from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    db_host: str = os.getenv("db_host", "localhost")
    db_port: int = int(os.getenv("db_port", 5432))
    db_name: str = os.getenv("db_name", "antifraud")
    db_user: str = os.getenv("db_user", "postgres")
    db_password: str = os.getenv("db_password", "password")
    redis_host: str = os.getenv("redis_host", "localhost")
    redis_port: int = int(os.getenv("redis_port", 6379))
    random_secret: str = os.getenv("random_secret", "default_secret_for_dev")
    admin_email: str = os.getenv("admin_email", "admin@admin.com")
    admin_fullname: str = os.getenv("admin_fullname", "admin user")
    admin_password: str = os.getenv("admin_password", "admin123")

settings = Settings()