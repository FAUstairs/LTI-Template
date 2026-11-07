"""HTTP routes for the LTI tool."""

from __future__ import annotations

import secrets
from urllib.parse import urlencode

import jwt
import requests
from flask import Blueprint, current_app, redirect, request, session

from config import Settings
from rendering import error_page, html_page, launch_page
from security import tool_public_jwk, validate_launch_token


routes = Blueprint("routes", __name__)


def settings() -> Settings:
    """Return the settings stored on the current Flask application."""
    return current_app.config["LTI_SETTINGS"]


@routes.get("/")
def index():
    """Show the landing page for direct browser requests."""
    return html_page(
        "LTI-External-Tool",
        "<h1>LTI-External-Tool</h1>"
        "<p>Launch this tool from your learning platform.</p>",
    )


@routes.get("/jwks")
def jwks():
    """Expose the tool's public key set to the LTI platform."""
    try:
        return {"keys": [tool_public_jwk(settings())]}
    except (OSError, ValueError, RuntimeError) as error:
        return error_page(f"Invalid public key configuration: {error}", 500)


@routes.route("/lti/login", methods=["GET", "POST"])
def login():
    """Start the OIDC login flow initiated by the LTI platform."""
    app_settings = settings()
    parameters = request.values
    issuer = parameters.get("iss")
    login_hint = parameters.get("login_hint")
    target_link_uri = parameters.get("target_link_uri", request.url_root)
    lti_message_hint = parameters.get("lti_message_hint")
    if not issuer or not login_hint:
        return error_page("iss and login_hint are required.")
    if issuer != app_settings.platform_issuer:
        return error_page("Unknown LTI platform issuer.", 403)

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    session["oidc_state"] = state
    session["oidc_nonce"] = nonce
    session["target_link_uri"] = target_link_uri

    params = {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "client_id": app_settings.client_id,
        "redirect_uri": app_settings.redirect_uri,
        "login_hint": login_hint,
        "state": state,
        "nonce": nonce,
        "prompt": "none",
    }
    if lti_message_hint:
        params["lti_message_hint"] = lti_message_hint
    return redirect(
        app_settings.platform_authorization_endpoint + "?" + urlencode(params)
    )


@routes.post("/lti/launch")
def launch():
    """Validate the OIDC response and display the user's launch claims."""
    app_settings = settings()
    state = request.form.get("state")
    token = request.form.get("id_token")
    expected_state = session.pop("oidc_state", None)
    expected_nonce = session.pop("oidc_nonce", None)
    if not state or not secrets.compare_digest(state, expected_state or ""):
        return error_page("Invalid OIDC state.", 403)
    if not token:
        return error_page("The LTI ID token is missing.")

    try:
        claims = validate_launch_token(token, app_settings)
    except (jwt.PyJWTError, requests.RequestException, ValueError, RuntimeError) as error:
        return error_page(f"Launch validation failed: {error}", 403)
    if not expected_nonce or claims.get("nonce") != expected_nonce:
        return error_page("Invalid OIDC nonce.", 403)
    return launch_page(app_settings.text, claims)
