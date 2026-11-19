"""GitHub for docs pull requests: a small API client and a safe branch push."""

from .client import GithubClient, GithubError, graphql_url, web_git_url
from .push import push_branch

__all__ = ["GithubClient", "GithubError", "graphql_url", "push_branch", "web_git_url"]
