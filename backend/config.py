import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")


def get_settings() -> Settings:
    return Settings()
