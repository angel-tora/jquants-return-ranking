from __future__ import annotations

import getpass
import os
import stat
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

try:
    from platformdirs import user_config_dir
except ImportError:  # pragma: no cover
    user_config_dir = None

APP_NAME = "jquants-return-ranking"
API_KEY_ENV = "JQUANTS_API_KEY"


@dataclass(frozen=True)
class ApiKeyResult:
    api_key: str | None
    source: str
    config_path: Path


def config_dir() -> Path:
    if user_config_dir is None:
        return Path.home() / ".config" / APP_NAME
    return Path(user_config_dir(APP_NAME))


def config_path() -> Path:
    return config_dir() / "config.toml"


def load_api_key(path: Path | None = None) -> ApiKeyResult:
    path = path or config_path()
    env_key = os.getenv(API_KEY_ENV, "")
    if env_key:
        return ApiKeyResult(api_key=env_key, source="env", config_path=path)
    saved_key = str(read_config(path).get("jquants", {}).get("api_key", "") or "")
    if saved_key:
        return ApiKeyResult(api_key=saved_key, source="config", config_path=path)
    return ApiKeyResult(api_key=None, source="missing", config_path=path)


def require_api_key(save: bool = False, path: Path | None = None) -> ApiKeyResult:
    loaded = load_api_key(path)
    if loaded.api_key:
        return loaded
    api_key = getpass.getpass("J-Quants API key: ").strip()
    if not api_key:
        raise ValueError("API key must not be empty.")
    if save:
        saved_path = save_api_key(api_key, loaded.config_path)
        return ApiKeyResult(api_key=api_key, source="prompt_saved", config_path=saved_path)
    return ApiKeyResult(api_key=api_key, source="prompt", config_path=loaded.config_path)


def read_config(path: Path | None = None) -> dict:
    path = path or config_path()
    if not path.exists():
        return {}
    if tomllib is not None:
        with path.open("rb") as handle:
            payload = tomllib.load(handle)
        return payload if isinstance(payload, dict) else {}
    return _read_simple_toml(path)


def _read_simple_toml(path: Path) -> dict:
    result: dict[str, dict[str, str]] = {}
    section = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            result.setdefault(section, {})
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result.setdefault(section, {})[key.strip()] = value.strip().strip('"')
    return result


def save_api_key(api_key: str, path: Path | None = None) -> Path:
    api_key = api_key.strip()
    if not api_key:
        raise ValueError("API key must not be empty.")
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.parent.chmod(stat.S_IRWXU)
    except OSError:
        pass
    path.write_text("[jquants]\n" f'api_key = "{_toml_escape(api_key)}"\n', encoding="utf-8")
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    return path


def prompt_and_save_api_key(path: Path | None = None) -> Path:
    return save_api_key(getpass.getpass("J-Quants API key: "), path)


def _toml_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
