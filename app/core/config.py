from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_backend: str = "sqlite"  # mongo | sqlite

    sqlite_path: str = "./dev.db"

    bootstrap_admin_email: str = "admin@local"
    bootstrap_admin_password: str = "Admin12345!"

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "afcalink_internal"

    session_secret: str = "CHANGE_ME"
    cookie_https_only: bool = False


settings = Settings()
