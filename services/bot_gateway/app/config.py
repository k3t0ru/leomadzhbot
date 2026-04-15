import os


BOT_TOKEN = "BOT_TOKEN_PLACEHOLDER"


class Settings:
    def __init__(self) -> None:
        self.profile_service_base_url = os.getenv(
            "PROFILE_SERVICE_BASE_URL", "http://localhost:8000"
        )


settings = Settings()
