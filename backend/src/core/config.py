"""Environment configuration loader."""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        self.better_auth_secret: str = os.getenv("BETTER_AUTH_SECRET", "")
        self.database_url: str = os.getenv("DATABASE_URL", "")
        self.host: str = os.getenv("HOST", "0.0.0.0")
        self.port: int = int(os.getenv("PORT", "8000"))
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

        # MCP Server Configuration (Phase 3)
        self.mcp_host: str = os.getenv("MCP_HOST", "localhost")
        self.mcp_port: int = int(os.getenv("MCP_PORT", "8001"))
        self.mcp_debug: bool = os.getenv("MCP_DEBUG", "false").lower() == "true"

        # Validate required settings
        if not self.better_auth_secret:
            raise ValueError("BETTER_AUTH_SECRET environment variable is required")
        if len(self.better_auth_secret) < 32:
            raise ValueError("BETTER_AUTH_SECRET must be at least 32 characters")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
