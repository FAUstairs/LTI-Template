"""JWT and JWKS handling."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import jwt
import requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from config import Settings


def base64url_uint(value: int) -> str:
    """Encode an integer in the Base64URL format used by JWK values."""
    byte_length = (value.bit_length() + 7) // 8
    return jwt.utils.base64url_encode(value.to_bytes(byte_length, "big")).decode()


def tool_public_jwk(settings: Settings) -> dict[str, str]:
    """Return the tool's public RSA key as a JSON Web Key."""
    return _tool_public_jwk(settings.tool_public_key_path, settings.tool_key_id)


@lru_cache(maxsize=4)
def _tool_public_jwk(
    public_key_path: str,
    key_id: str,
) -> dict[str, str]:
    """Load and convert the configured PEM public key into a JWK."""
    with open(public_key_path, "rb") as public_key_file:
        public_key = serialization.load_pem_public_key(public_key_file.read())
    if not isinstance(public_key, RSAPublicKey):
        raise RuntimeError("The tool public key must be an RSA key.")

    numbers = public_key.public_numbers()
    return {
        "kty": "RSA",
        "n": base64url_uint(numbers.n),
        "e": base64url_uint(numbers.e),
        "alg": "RS256",
        "use": "sig",
        "kid": key_id,
    }


@lru_cache(maxsize=4)
def platform_keys(jwks_url: str) -> dict[str, Any]:
    """Fetch and cache the platform's public JWKS document."""
    response = requests.get(jwks_url, timeout=10)
    response.raise_for_status()
    return response.json()


def select_signing_key(token: str, jwks_url: str) -> dict[str, Any]:
    """Find the platform key matching the token's key ID."""
    key_id = jwt.get_unverified_header(token).get("kid")
    if not key_id:
        raise ValueError("The ID token does not contain a key ID.")

    for key in platform_keys(jwks_url).get("keys", []):
        if key.get("kid") == key_id:
            return key
    platform_keys.cache_clear()
    for key in platform_keys(jwks_url).get("keys", []):
        if key.get("kid") == key_id:
            return key
    raise ValueError("The signing key for the ID token was not found.")


def validate_launch_token(token: str, settings: Settings) -> dict[str, Any]:
    """Verify an LTI launch token and return its claims."""
    key = jwt.PyJWK.from_dict(
        select_signing_key(token, settings.platform_jwks_url)
    ).key
    return jwt.decode(
        token,
        key,
        algorithms=["RS256"],
        audience=settings.client_id,
        issuer=settings.platform_issuer,
        options={"require": ["iss", "sub", "aud", "exp", "iat", "nonce"]},
    )
