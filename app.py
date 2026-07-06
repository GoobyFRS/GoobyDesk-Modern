#!/usr/bin/env python3
# Primary GoobyDesk_Modern entry point
import os
import json
import threading
import time
import logging
import requests

from dotenv import load_dotenv
from datetime import timedelta

import local_config_loader

BUILDID="v0.0.1-alpha"

# Secrets loaded from .env file
load_dotenv(dotenv_path=".env")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
CF_TURNSTILE_SITE_KEY = os.getenv("CF_TURNSTILE_SITE_KEY")
CF_TURNSTILE_SECRET_KEY = os.getenv("CF_TURNSTILE_SECRET_KEY")

# Configuration non-secret data loaded from YAML
core_yaml_config = local_config_loader.load_core_config()
TICKETS_FILE: str = core_yaml_config["tickets_file"]
EMPLOYEE_FILE: str = core_yaml_config["employee_file"]
LOG_LEVEL: str = core_yaml_config["logging"]["level"]
LOG_FILE: str = core_yaml_config["logging"]["file"]
EMAIL_ENABLED: bool = core_yaml_config["email"]["enabled"]
EMAIL_ACCOUNT: str = core_yaml_config["email"]["account"]
IMAP_SERVER: str = core_yaml_config["email"]["imap_server"]
SMTP_SERVER: str = core_yaml_config["email"]["smtp_server"]
SMTP_PORT: int = core_yaml_config["email"]["smtp_port"]

# Flask App core setup and configuration
app = Flask(__name__)
app.secret_key = os.getenv("FLASKAPP_SECRET_KEY")
app.permanent_session_lifetime = timedelta(hours=24)

app.config.update(
    SESSION_COOKIE_NAME="goobydesk_session_cookie",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=not app.debug,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_REFRESH_EACH_REQUEST=True,
    PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)

@app.after_request
def set_security_headers(response: Response) -> Response:
    """Add security headers to all HTTP responses.

    Args:
        response: The Flask response object.

    Returns:
        The response with security headers added.
    """
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.bunny.net; "
        "img-src 'self' data: https:; "
        "font-src 'self' data: https://fonts.bunny.net; "
        "connect-src 'self'; "
        "frame-src https://challenges.cloudflare.com; "
        "frame-ancestors 'none'"
    )
    if not app.debug:
        response.headers["Strict-Transport-Security"] = (
            "max-age=86400; includeSubDomains; preload"
        )
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    return response


logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(levelname)s - %(module)s/%(funcName)s - %(message)s"
)

@app.errorhandler(400)
def bad_request(e: Exception) -> tuple[str, int]:
    """Handle 400 Bad Request errors.

    Args:
        e: The exception that triggered the error.

    Returns:
        Rendered 400 error template.
    """
    return render_template("400.html"), 400


@app.errorhandler(403)
def forbidden(e: Exception) -> tuple[str, int]:
    """Handle 403 Forbidden errors.

    Args:
        e: The exception that triggered the error.

    Returns:
        Rendered 403 error template.
    """
    return render_template("403.html"), 403


@app.errorhandler(404)
def page_not_found(e: Exception) -> tuple[str, int]:
    """Handle 404 Not Found errors.

    Args:
        e: The exception that triggered the error.

    Returns:
        Rendered 404 error template.
    """
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e: Exception) -> tuple[str, int]:
    """Handle 500 Internal Server errors.

    Args:
        e: The exception that triggered the error.

    Returns:
        Rendered 500 error template.
    """
    logging.critical(f"Internal Server Error: {e}")
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run()