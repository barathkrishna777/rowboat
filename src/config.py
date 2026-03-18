import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Providers
    gemini_api_key: str = ""
    google_api_key: str = ""  # Alias — PydanticAI reads GOOGLE_API_KEY
    groq_api_key: str = ""

    # Venue APIs
    yelp_api_key: str = ""
    eventbrite_api_key: str = ""
    ticketmaster_api_key: str = ""

    # Google Calendar OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # App Settings
    database_url: str = "sqlite+aiosqlite:///./data/outing_planner.db"
    chroma_persist_dir: str = "./data/chroma_db"
    default_location: str = "Pittsburgh, PA"

    # LLM Settings
    primary_model: str = "google-gla:gemini-2.5-flash"
    fallback_model: str = "groq:llama-3.3-70b-versatile"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def sync_api_keys(self):
        """Ensure GOOGLE_API_KEY is set for PydanticAI from either env var."""
        key = self.google_api_key or self.gemini_api_key
        if key:
            os.environ["GOOGLE_API_KEY"] = key


settings = Settings()
settings.sync_api_keys()
