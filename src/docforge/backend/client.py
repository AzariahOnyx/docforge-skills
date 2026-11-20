"""One streaming Messages API call per stage, with retries and refusal handling.

The API key comes from the environment variable named in config (default
ANTHROPIC_API_KEY), passed to the client explicitly; if it is unset, the SDK's
own credential chain is used (for example an `ant auth login` profile). The key
is never written to run files, logs or error messages.

Tests pass a fake client with the same `beta.messages.stream(...)` shape, so no
test makes a network call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
import time

from docforge.config import Backend

FALLBACK_BETA = "server-side-fallback-2026-07-01"
STREAM_ATTEMPTS = 3
BACKOFF_SECONDS = (2.0, 8.0)


class BackendError(Exception):
    """A stage could not be run through the API. Never contains credentials."""


class TransientError(Exception):
    """A dropped connection or stream that is worth retrying (also raised by test fakes)."""


@dataclass
class CallResult:
    data: dict
    model_requested: str
    model_served: str
    request_id: str | None
    stop_reason: str | None
    usage: dict
    iterations: list[dict]
    duration_s: float
    content: list = field(default_factory=list)  # the assistant content, replayed unchanged on a repair turn


def make_client(backend: Backend):
    try:
        import anthropic
    except ImportError:
        raise BackendError("the Anthropic SDK is not installed; run `uv sync --extra api`") from None
    key = os.environ.get(backend.api_key_env)
    return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()


def _retryable() -> tuple[type[BaseException], ...]:
    errors: list[type[BaseException]] = [TransientError]
    try:
        import anthropic

        errors += [anthropic.APIConnectionError, anthropic.InternalServerError]
        for name in ("OverloadedError", "ServiceUnavailableError"):
            if hasattr(anthropic, name):
                errors.append(getattr(anthropic, name))
    except ImportError:
        pass
    return tuple(errors)


def _plain(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json", exclude_none=True)
    if hasattr(obj, "__dict__"):
        return {k: _plain(v) for k, v in vars(obj).items() if not k.startswith("_")}
    return str(obj)


def _is_sdk_error(exc: BaseException) -> bool:
    try:
        import anthropic
    except ImportError:
        return False
    return isinstance(exc, anthropic.AnthropicError)


def _translate(exc: BaseException, backend: Backend) -> BackendError:
    try:
        import anthropic
    except ImportError:
        return BackendError(f"API call failed: {type(exc).__name__}")
    if isinstance(exc, (anthropic.AuthenticationError, getattr(anthropic, "CredentialsError", ()))):
        return BackendError(f"no valid API credentials: set {backend.api_key_env} or run `ant auth login`")
    if isinstance(exc, anthropic.PermissionDeniedError):
        return BackendError("the API key lacks permission for this request")
    if isinstance(exc, anthropic.RateLimitError):
        return BackendError("rate limited by the API; try again later")
    if isinstance(exc, anthropic.NotFoundError):
        return BackendError("model or endpoint not found; check backend.model")
    if isinstance(exc, anthropic.BadRequestError):
        return BackendError(f"the API rejected the request: {getattr(exc, 'message', '')}")
    if isinstance(exc, anthropic.APIStatusError):
        return BackendError(f"API error (HTTP {exc.status_code})")
    return BackendError(f"API call failed: {type(exc).__name__}")


def request_params(backend: Backend, *, model: str, effort: str, max_tokens: int, system: list[dict],
                   messages: list[dict], schema: dict) -> dict:
    """The request body (no credentials). Adaptive thinking is the default when `thinking` is omitted."""
    params = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    }
    # Haiku has no server-side fallback.
    if backend.fallbacks and not model.startswith("claude-haiku"):
        params["betas"] = [FALLBACK_BETA]
        params["fallbacks"] = "default"
    return params


def call(client, backend: Backend, params: dict, *, sleep=time.sleep, expect_files: bool = True) -> CallResult:
    retryable = _retryable()
    started = time.monotonic()
    for attempt in range(1, STREAM_ATTEMPTS + 1):
        try:
            with client.beta.messages.stream(**params) as stream:
                final = stream.get_final_message()
            break
        except BackendError:
            raise
        except retryable:
            if attempt == STREAM_ATTEMPTS:
                raise BackendError(f"the API stream failed {attempt} times; try again later") from None
            sleep(BACKOFF_SECONDS[attempt - 1])
        except Exception as exc:  # SDK errors: translate without echoing request contents
            if _is_sdk_error(exc):
                raise _translate(exc, backend) from None
            if isinstance(exc, TypeError) and "authentication" in str(exc).lower():
                # The SDK raises TypeError when it finds no credentials at all.
                raise BackendError(f"no valid API credentials: set {backend.api_key_env} or run `ant auth login`") from None
            raise
    duration = time.monotonic() - started

    usage = _plain(getattr(final, "usage", None)) or {}
    result = CallResult(
        data={}, model_requested=params["model"], model_served=getattr(final, "model", params["model"]),
        request_id=getattr(final, "_request_id", None) or getattr(final, "id", None),
        stop_reason=getattr(final, "stop_reason", None), usage=usage,
        iterations=list(usage.get("iterations") or []), duration_s=round(duration, 2),
        content=list(getattr(final, "content", []) or []),
    )
    if result.stop_reason == "refusal":
        details = _plain(getattr(final, "stop_details", None)) or {}
        raise BackendError(f"the model declined this stage (category: {details.get('category') or 'not given'})")
    if result.stop_reason == "max_tokens":
        raise BackendError("the answer hit max_tokens before it was complete; raise backend.max_tokens")
    text = next((getattr(b, "text", "") for b in result.content if getattr(b, "type", None) == "text"), "")
    try:
        data = json.loads(text)
    except ValueError:
        raise BackendError("the answer was not valid JSON") from None
    if not isinstance(data, dict) or (expect_files and not isinstance(data.get("files"), list)):
        raise BackendError("the answer did not contain a files list" if expect_files else "the answer was not an object")
    result.data = data
    return result
