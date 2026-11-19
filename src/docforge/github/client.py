"""A small GitHub client for docs pull requests: REST for pull requests and comments, GraphQL to mark a
draft ready (the REST API has no call for that).

Safety rules:
- requests go only to the configured API URL's scheme and host; redirects are refused;
- the token is read from the environment variable named in the doc collection, sent only in the
  Authorization header, and never written to errors, logs or files;
- responses larger than MAX_RESPONSE_BYTES are refused.

Tests point `api_url` at a local stub server, so no test reaches GitHub.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from docforge.config import DocCollection

MAX_RESPONSE_BYTES = 5 * 1024 * 1024
TIMEOUT_SECONDS = 30
USER_AGENT = "docforge-publish"


class GithubError(Exception):
    """A GitHub call failed. Messages never contain the token."""


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GithubError("refused a redirect from the GitHub API")


def graphql_url(api_url: str) -> str:
    """GitHub.com: <api>/graphql. GitHub Enterprise Server: https://host/api/v3 -> https://host/api/graphql."""
    if api_url.endswith("/api/v3"):
        return api_url[: -len("/v3")] + "/graphql"
    return api_url + "/graphql"


def web_git_url(api_url: str, repo: str) -> str:
    """The HTTPS clone URL for a repository on the same GitHub as `api_url`."""
    parts = urlsplit(api_url)
    host = parts.netloc
    if host == "api.github.com":
        host = "github.com"
    return f"{parts.scheme}://{host}/{repo}.git"


def _repo_path(repo: str) -> str:
    owner, _, name = repo.partition("/")
    return f"/repos/{quote(owner, safe='')}/{quote(name, safe='')}"


class GithubClient:
    def __init__(self, collection: DocCollection, *, max_bytes: int = MAX_RESPONSE_BYTES):
        self.api_url = collection.api_url
        self.origin = urlsplit(self.api_url)[:2]
        token = os.environ.get(collection.token_env)
        if not token:
            raise GithubError(f"environment variable {collection.token_env} is not set")
        self._auth = f"Bearer {token}"
        self.max_bytes = max_bytes
        self._opener = build_opener(_NoRedirects())

    def _call(self, method: str, url: str, body: dict | None = None):
        if urlsplit(url)[:2] != self.origin:
            raise GithubError("refused a request to another host")
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(url, method=method, data=data, headers={
            "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": USER_AGENT, **({"Content-Type": "application/json"} if data else {})})
        request.add_unredirected_header("Authorization", self._auth)
        where = f"{method} {urlsplit(url).path}"
        try:
            with self._opener.open(request, timeout=TIMEOUT_SECONDS) as response:
                raw = response.read(self.max_bytes + 1)
        except GithubError:
            raise
        except HTTPError as exc:
            hint = {401: " (check the token)", 403: " (no permission, or rate limited)", 404: " (not found or no access)",
                    422: " (GitHub rejected the request)"}
            raise GithubError(f"{where} returned HTTP {exc.code}{hint.get(exc.code, '')}") from None
        except (URLError, OSError) as exc:
            raise GithubError(f"{where} failed: {type(getattr(exc, 'reason', exc)).__name__}") from None
        if len(raw) > self.max_bytes:
            raise GithubError(f"{where} returned more than {self.max_bytes} bytes; refused")
        if not raw.strip():
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            raise GithubError(f"{where} did not return JSON") from None

    def rest(self, method: str, path: str, body: dict | None = None, query: dict | None = None):
        url = self.api_url + path + (("?" + urlencode(query)) if query else "")
        return self._call(method, url, body)

    # --- pull requests ------------------------------------------------------------

    def find_pr(self, repo: str, branch: str) -> dict | None:
        """The pull request (any state) whose head is `branch` in the same repository, or None."""
        owner = repo.split("/", 1)[0]
        found = self.rest("GET", _repo_path(repo) + "/pulls", query={"head": f"{owner}:{branch}", "state": "all"})
        if not isinstance(found, list):
            raise GithubError("listing pull requests did not return a list")
        return found[0] if found else None

    def create_pr(self, repo: str, *, base: str, head: str, title: str, body: str, draft: bool) -> dict:
        pr = self.rest("POST", _repo_path(repo) + "/pulls",
                       {"base": base, "head": head, "title": title, "body": body, "draft": draft})
        if not isinstance(pr, dict) or not pr.get("number"):
            raise GithubError("creating the pull request did not return a pull request")
        return pr

    def get_pr(self, repo: str, number: int) -> dict:
        return self.rest("GET", _repo_path(repo) + f"/pulls/{int(number)}")

    def update_pr(self, repo: str, number: int, *, body: str | None = None, title: str | None = None) -> dict:
        fields = {k: v for k, v in (("body", body), ("title", title)) if v is not None}
        return self.rest("PATCH", _repo_path(repo) + f"/pulls/{int(number)}", fields)

    def comment(self, repo: str, number: int, body: str) -> dict:
        return self.rest("POST", _repo_path(repo) + f"/issues/{int(number)}/comments", {"body": body})

    def mark_ready(self, node_id: str) -> bool:
        """Mark a draft pull request ready for review. Returns the new draft state (False when done)."""
        query = ("mutation($id: ID!) { markPullRequestReadyForReview(input: {pullRequestId: $id}) "
                 "{ pullRequest { isDraft } } }")
        result = self._call("POST", graphql_url(self.api_url), {"query": query, "variables": {"id": node_id}})
        if not isinstance(result, dict) or result.get("errors"):
            raise GithubError("GitHub refused to mark the pull request ready")
        try:
            return bool(result["data"]["markPullRequestReadyForReview"]["pullRequest"]["isDraft"])
        except (KeyError, TypeError):
            raise GithubError("marking the pull request ready returned an unexpected answer") from None
