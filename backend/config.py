import os
import base64
import secrets
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Determine project base directory
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = PROJECT_ROOT / '.env'

def _generate_default_fernet_key() -> str:
    """
    Generate a url-safe base64-encoded 32-byte key for Fernet encryption.
    """
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')

class Settings(BaseSettings):
    """
    Centralized, type-safe application settings.
    Automatically loads configuration from:
    1. System environment variables
    2. .env file in project root
    3. Secure defaults
    """
    # Encryption Master Key for Fernet Secrets Vault
    SECRET_KEY: str = Field(
        default_factory=_generate_default_fernet_key,
        description="Master encryption key for local credentials at rest"
    )

    # JWT Session Token Secret
    JWT_SECRET: str = Field(
        default="healthpulse-jwt-super-secure-key-change-in-prod-2026",
        description="Secret key used for signing JWT session tokens"
    )

    # Global Fallback Google Gemini API Key
    GEMINI_API_KEY: str = Field(
        default="",
        description="Global fallback Gemini API key for scale photo parsing"
    )

    # WebAuthn / Passkey Relying Party Domain
    RP_ID: str = Field(
        default="localhost",
        description="Relying party domain ID for WebAuthn passkeys"
    )
    RP_NAME: str = Field(
        default="HealthPulse Tracker",
        description="Relying party display name"
    )

    # Server Network Configuration
    HOST: str = Field(default="0.0.0.0", description="Bind host address")
    PORT: int = Field(default=5000, description="Bind port number")
    ENABLE_SSL: bool = Field(default=False, description="Enable HTTPS server mode")

    # SSL Certificate Paths
    SSL_CERT_PATH: Optional[str] = Field(default=None, description="Custom SSL certificate path")
    SSL_KEY_PATH: Optional[str] = Field(default=None, description="Custom SSL private key path")

    # Database Configuration
    DB_PATH: str = Field(
        default=str(BACKEND_DIR / "tracker.db"),
        description="Path to SQLite database file"
    )

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate singleton settings instance
settings = Settings()
