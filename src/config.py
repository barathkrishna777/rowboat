import logging
import os

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


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

    # Auth / JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week

    # App Settings
    environment: str = "development"  # "development" | "production"
    database_url: str = "sqlite+aiosqlite:///./data/rowboat.db"
    chroma_persist_dir: str = "./data/chroma_db"
    default_location: str = "Pittsburgh, PA"
    default_timezone: str = "America/New_York"

    # LLM Settings
    primary_model: str = "anthropic:claude-haiku-3-5"
    fallback_model: str = "google-gla:gemini-2.5-flash"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def validate_production(self) -> None:
        """Warn about missing or insecure settings in production (non-fatal)."""
        if self.environment != "production":
            return

        if self.jwt_secret == "change-me-in-production" or len(self.jwt_secret) < 16:
            logger.warning(
                "JWT_SECRET is using the default or is too short — "
                "set a secure value (>= 16 chars) via the JWT_SECRET env var"
            )

        if "sqlite" in self.database_url:
            logger.warning(
                "DATABASE_URL is SQLite in production — this is unsafe for "
                "multi-worker deployments. Set a PostgreSQL URL."
            )

        if not (self.gemini_api_key or self.google_api_key or self.anthropic_api_key):
            logger.warning(
                "No LLM API key is configured — set ANTHROPIC_API_KEY or "
                "GOOGLE_API_KEY. AI features will not work."
            )

    def sync_api_keys(self):
        """Ensure provider env vars are set for PydanticAI from settings.

        PydanticAI reads GOOGLE_API_KEY and ANTHROPIC_API_KEY directly from
        the environment — this method pushes the loaded settings values back
        into os.environ so the provider SDKs always see the correct keys.
        """
        # Google / Gemini
        key = self.gemini_api_key or self.google_api_key
        if key:
            os.environ["GOOGLE_API_KEY"] = key
            self.google_api_key = key

        # Anthropic / Claude
        if self.anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.anthropic_api_key


settings = Settings()
# Workaround: pydantic-settings sometimes misses newly added .env fields
if not settings.anthropic_api_key:
    from dotenv import dotenv_values
    _env = dotenv_values(".env")
    if _env.get("ANTHROPIC_API_KEY"):
        settings.anthropic_api_key = _env["ANTHROPIC_API_KEY"]
settings.sync_api_keys()
# validate_production() is called in the FastAPI startup event (src/main.py)
# so it does not prevent the app from booting and serving /health.
