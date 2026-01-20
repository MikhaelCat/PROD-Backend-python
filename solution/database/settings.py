from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", 5432))
    db_name: str = os.getenv("DB_NAME", "antifraud")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "password")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", 6379))
    random_secret: str = os.getenv("RANDOM_SECRET", "default_secret_for_dev")
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@admin.com")
    admin_fullname: str = os.getenv("ADMIN_FULLNAME", "admin user")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")

settings = Settings()