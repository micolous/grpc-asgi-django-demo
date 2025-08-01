"""
Miscellaneous utility functions.
"""

import functools
import os
from pathlib import Path
from typing import TypeVar

_SECRET_ROOT = Path("/run/secrets")
_MAX_ENVIRONMENT_LENGTH = 64 << 10  # is enough for anyone
_T = TypeVar("_T")


def get_env_or_secret(key: str, default: _T = None) -> str | _T:
    """Get the environment variable `key`, or load it from `/run/secrets/{key}`.

    This allows environment variables to be passed as regular environment
    variables, or as Docker secrets.

    Environment variables take priority.
    """

    if not key:
        raise ValueError("Cannot read from empty environment variable name")

    if "/" in key or "\\" in key:
        raise ValueError(
            "Environment variable names may not contain directory separators"
        )

    v = os.getenv(key)

    if v is None:
        try:
            with open(_SECRET_ROOT / key, "r") as f:
                v = f.read(_MAX_ENVIRONMENT_LENGTH)
        except BaseException:
            # Silently ignore errors, we can rethrow later.
            return default

    return v


def require_env(key: str) -> str:
    """
    Get the environment variable `key`.

    Raises:
        ValueError: If the environment variable `key` is not set or empty.
    """
    v = get_env_or_secret(key)
    if not v:
        raise ValueError(f"Missing environment variable: {key}")

    return v


class LazyRequireEnv:
    """`require_env()` that evaluates on `__str__`.

    If the environment variable is unset or empty, `__str__` raises
    `ValueError`.

    The result is cached.

    The idea of this is that it makes an environment variable required, but only
    if it's actually needed by something.
    """

    def __init__(self, key: str):
        self._key = key

    @functools.cache
    def __str__(self) -> str:
        return require_env(self._key)

    @functools.cache
    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        v = str(self)
        return v.encode(encoding=encoding, errors=errors)


class LazyEnv:
    """Get an environment variable when first evaluating `__str__`.

    If the environment variable is unset, `__str__` returns the default value.

    The result is cached.
    """

    def __init__(self, key: str, default: str = ""):
        self._key = key
        self._default = default

    @functools.cache
    def __str__(self) -> str:
        return get_env_or_secret(self._key, self._default)

    @functools.cache
    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        v = str(self)
        return v.encode(encoding=encoding, errors=errors)
