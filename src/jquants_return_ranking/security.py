from __future__ import annotations

import re
from collections.abc import Iterable

REDACTED = "[REDACTED]"

_SECRET_PATTERNS = (
    re.compile(r'(?i)(x-api-key\s*[:=]\s*)("[^"]*"|\'[^\']*\'|[^\s,;]+)'),
    re.compile(r'(?i)(api[_-]?key\s*[:=]\s*)("[^"]*"|\'[^\']*\'|[^\s,;]+)'),
    re.compile(r'(?i)(JQUANTS_API_KEY\s*=\s*)("[^"]*"|\'[^\']*\'|[^\s,;]+)'),
    re.compile(r'(?i)(Authorization\s*:\s*Bearer\s+)("[^"]*"|\'[^\']*\'|[^\s,;]+)'),
)


def sanitize_text(value: object, secrets: Iterable[str | None] = ()) -> str:
    """Return a display-safe string with API keys and common token fields hidden."""
    text = str(value)
    for secret in secrets:
        if secret and len(secret) >= 4:
            text = text.replace(secret, REDACTED)
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}{REDACTED}", text)
    return text
