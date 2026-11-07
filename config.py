"""Application configuration for the LTI tool."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    platform_issuer: str
    client_id: str
    deployment_id: str
    platform_jwks_url: str
    platform_authorization_endpoint: str
    redirect_uri: str
    tool_public_key_path: str
    tool_key_id: str
    flask_secret_key: str
    text: str
    host: str
    port: int


def _env(name: str, default: str | None = None) -> str:
    """Read a required setting, using the supplied default when available."""
    value = os.environ.get(name, default)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set.")
    return value


def load_settings() -> Settings:
    """Load application settings from environment variables and defaults."""
    return Settings(
        platform_issuer=_env("LTI_PLATFORM_ISSUER", "http://localhost"),
        client_id=_env("LTI_CLIENT_ID", "W4QaDa1kw3EDGp6"),
        deployment_id=_env("LTI_DEPLOYMENT_ID", "1"),
        platform_jwks_url=_env(
            "LTI_PLATFORM_JWKS_URL",
            "http://localhost/Modules/LTIConsumer/lticerts.php",
        ),
        platform_authorization_endpoint=_env(
            "LTI_PLATFORM_AUTHORIZATION_ENDPOINT",
            "http://localhost/Modules/LTIConsumer/ltiauth.php",
        ),
        redirect_uri=_env(
            "LTI_REDIRECT_URI",
            "http://localhost:5000/lti/launch",
        ),
        tool_public_key_path=_env(
            "LTI_TOOL_PUBLIC_KEY_PATH",
            str(BASE_DIR / "keys" / "lti-public.pem"),
        ),
        tool_key_id=_env("LTI_TOOL_KEY_ID", "main"),
        flask_secret_key=_env("FLASK_SECRET_KEY"),
        text=os.environ.get("LTI_TEXT", "Welcome to the LTI external tool."),
        host=os.environ.get("HOST", "localhost"),
        port=int(os.environ.get("PORT", "5000")),
    )
