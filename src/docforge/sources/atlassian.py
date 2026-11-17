"""A small read-only HTTP client for Jira and Confluence.

Safety rules:
- only GET requests, only to the configured base URL's scheme and host;
- a redirect to any other scheme or host is refused;
- responses larger than MAX_RESPONSE_BYTES are refused;
- credentials are read from environment variables named in the config, sent
  only in the Authorization header, and never written to errors, logs or files.
"""

from __future__ import annotations

import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from docforge.config import AtlassianSource, check_service_url

MAX_RESPONSE_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 30
USER_AGENT = "docforge-source-fetch"


class SourceFetchError(Exception):
    """Raised when a source cannot be fetched. Messages never contain credentials."""


def _origin(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    return parts.scheme, parts.netloc.lower()


class _PinnedRedirects(HTTPRedirectHandler):
    def __init__(self, origin: tuple[str, str]):
        self.origin = origin

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if _origin(newurl) != self.origin:
            raise SourceFetchError(f"refused a redirect to another host ({urlsplit(newurl).netloc or 'unknown'})")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _auth_header(source: AtlassianSource) -> str | None:
    if not source.auth_token_env:
        return None
    token = os.environ.get(source.auth_token_env)
    if not token:
        raise SourceFetchError(f"environment variable {source.auth_token_env} is not set")
    if source.user_env:
        user = os.environ.get(source.user_env)
        if not user:
            raise SourceFetchError(f"environment variable {source.user_env} is not set")
        return "Basic " + base64.b64encode(f"{user}:{token}".encode()).decode()
    return f"Bearer {token}"


class AtlassianClient:
    def __init__(self, source: AtlassianSource, *, max_bytes: int = MAX_RESPONSE_BYTES):
        if not source.base_url:
            raise SourceFetchError("the source has no base_url in docforge.yaml")
        self.base_url = check_service_url(source.base_url)
        self.origin = _origin(self.base_url)
        self.max_bytes = max_bytes
        self._auth = _auth_header(source)
        self._opener = build_opener(_PinnedRedirects(self.origin))

    def url(self, path: str) -> str:
        """The base URL joined with a path. Path segments must already be quoted."""
        return self.base_url + "/" + path.lstrip("/")

    def get_json(self, path: str) -> dict:
        url = self.url(path)
        request = Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        if self._auth:
            request.add_unredirected_header("Authorization", self._auth)
        where = urlsplit(url).path
        try:
            with self._opener.open(request, timeout=TIMEOUT_SECONDS) as response:
                if _origin(response.geturl()) != self.origin:
                    raise SourceFetchError("response came from another host")
                body = response.read(self.max_bytes + 1)
        except SourceFetchError:
            raise
        except HTTPError as exc:
            hint = {401: " (check the credentials)", 403: " (no permission)", 404: " (not found or no access)"}
            raise SourceFetchError(f"GET {where} returned HTTP {exc.code}{hint.get(exc.code, '')}") from None
        except (URLError, OSError) as exc:
            reason = getattr(exc, "reason", exc)
            raise SourceFetchError(f"GET {where} failed: {type(reason).__name__}") from None
        if len(body) > self.max_bytes:
            raise SourceFetchError(f"GET {where} returned more than {self.max_bytes} bytes; refused")
        try:
            data = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise SourceFetchError(f"GET {where} did not return JSON") from None
        if not isinstance(data, dict):
            raise SourceFetchError(f"GET {where} did not return a JSON object")
        return data


def segment(value: str) -> str:
    return quote(value, safe="")
