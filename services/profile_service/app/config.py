import os


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://leomadzhbot:leomadzhbot@localhost:5432/leomadzhbot",
        )


settings = Settings()
