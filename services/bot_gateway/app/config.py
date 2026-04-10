import os


BOT_TOKEN = "8603422627:AAEm8-E0ULudQM_c0xsI0FtkS07Vg3J1BhA"


class Settings:
    def __init__(self) -> None:
        self.profile_service_base_url = os.getenv(
            "PROFILE_SERVICE_BASE_URL", "http://localhost:8000"
        )


settings = Settings()
