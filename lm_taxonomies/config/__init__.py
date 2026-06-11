"""Centralized lazy config loading using importlib.resources."""

import os
import json
from importlib import resources

_config_cache = {}


def load_config(filename: str, env_var: str = None) -> dict:
    """Load a JSON config file lazily with caching.

    Only reads from disk on first call. Subsequent calls return cached data.
    Respects environment variable override if provided.
    """
    if filename not in _config_cache:
        if env_var and os.environ.get(env_var):
            path = os.environ[env_var]
            with open(path) as f:
                _config_cache[filename] = json.load(f)
        else:
            _config_cache[filename] = json.loads(
                resources.files("lm_taxonomies.config").joinpath(filename).read_text()
            )

    return _config_cache[filename]
