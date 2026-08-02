from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_port: int = 10700
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_username: str = "resource_coordinator"
    db_password: SecretStr = SecretStr("resource_coordinator")
    db_name: str = "resource_coordinator"
    app_default_lease_ttl_minutes: int = 240
    app_max_lease_ttl_minutes: int = 480
    app_lease_cleanup_interval_minutes: int = 10
    app_lease_cleanup_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_username}:{self.db_password.get_secret_value()}"
            f"@{self.db_hostname}:{self.db_port}/{self.db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
