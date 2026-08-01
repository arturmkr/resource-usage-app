from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_port: int = 10700
    db_hostname: str = "localhost"
    db_port: int = 5432
    db_username: str = "userhub"
    db_password: SecretStr = SecretStr("userhub")
    db_name: str = "userhub"

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
