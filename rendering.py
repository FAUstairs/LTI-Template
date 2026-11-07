"""HTML rendering helpers."""

from __future__ import annotations

import html

from flask import Response


def html_page(title: str, body: str) -> Response:
    """Render a complete HTML page with the supplied title and body."""
    return Response(
        f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>
      body {{ font-family: system-ui, sans-serif; max-width: 48rem; margin: 3rem auto; padding: 0 1rem; }}
      dt {{ font-weight: 600; margin-top: .75rem; }}
      dd {{ margin: .15rem 0 0; overflow-wrap: anywhere; }}
      .error {{ color: #a00; }}
    </style>
  </head>
  <body>{body}</body>
</html>""",
        mimetype="text/html",
    )


def error_page(message: str, status: int = 400) -> tuple[Response, int]:
    """Render an escaped error message with the requested HTTP status."""
    return html_page(
        "LTI error",
        f'<p class="error">{html.escape(message)}</p>',
    ), status


def launch_page(text: str, claims: dict[str, object]) -> Response:
    """Render the configured text and selected claims from an LTI launch."""
    values = {
        "Name": claims.get("name"),
        "First name": claims.get("given_name"),
        "Last name": claims.get("family_name"),
        "Email": claims.get("email"),
        "User ID": claims.get("sub"),
        "Roles": claims.get(
            "https://purl.imsglobal.org/spec/lti/claim/roles"
        ),
    }
    details = "".join(
        f"<dt>{html.escape(label)}</dt>"
        f"<dd>{html.escape(str(value) if value is not None else '—')}</dd>"
        for label, value in values.items()
    )
    return html_page(
        "LTI-External-Tool",
        f"<h1>LTI-External-Tool</h1><p>{html.escape(text)}</p>"
        f"<h2>Launch data</h2><dl>{details}</dl>",
    )
