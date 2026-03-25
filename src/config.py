import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM Providers
    gemini_api_key: str = ""
    google_api_key: str = ""  # Alias — PydanticAI reads GOOGLE_API_KEY
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # Venue APIs
    yelp_api_key: str = ""
    eventbrite_api_key: str = ""
    ticketmaster_api_key: str = ""

    # Google Maps Embed
    google_maps_embed_key: str = ""

    # Google Calendar OAuth
    google_client_id: str = ""
    google_client_secret: str = ""

    # App Settings
    database_url: str = "sqlite+aiosqlite:///./data/outing_planner.db"
    chroma_persist_dir: str = "./data/chroma_db"
    default_location: str = "Pittsburgh, PA"
    default_timezone: str = "America/New_York"

    # LLM Settings
    primary_model: str = "google-gla:gemini-2.5-flash"
    fallback_model: str = "groq:llama-3.3-70b-versatile"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def sync_api_keys(self):
        """Ensure GOOGLE_API_KEY is set for PydanticAI from either env var.

        Prefers GEMINI_API_KEY — on Railway GOOGLE_API_KEY may be stale.
        """
        key = self.gemini_api_key or self.google_api_key
        if key:
            os.environ["GOOGLE_API_KEY"] = key
            # Also update the setting so all code paths use the correct key
            self.google_api_key = key


settings = Settings()
# Workaround: pydantic-settings sometimes misses newly added .env fields
if not settings.anthropic_api_key:
    from dotenv import dotenv_values
    _env = dotenv_values(".env")
    if _env.get("ANTHROPIC_API_KEY"):
        settings.anthropic_api_key = _env["ANTHROPIC_API_KEY"]
settings.sync_api_keys()
