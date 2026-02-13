"""Lightweight i18n support for MeshCore Hub.

Loads JSON translation files and provides a ``t()`` lookup function
that is shared between the Python (Jinja2) and JavaScript (SPA) sides.
The same ``en.json`` file is served as a static asset for the client and
read from disk for server-side template rendering.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_translations: dict[str, Any] = {}
_locale: str = "en"

# Directory where locale JSON files live (web/static/locales/)
LOCALES_DIR = Path(__file__).parent.parent / "web" / "static" / "locales"


def load_locale(locale: str = "en", locales_dir: Path | None = None) -> None:
    """Load a locale's translation file into memory.

    Args:
        locale: Language code (e.g. ``"en"``).
        locales_dir: Override directory containing ``<locale>.json`` files.
    """
    global _translations, _locale
    directory = locales_dir or LOCALES_DIR
    path = directory / f"{locale}.json"
    if not path.exists():
        logger.warning("Locale file not found: %s – falling back to 'en'", path)
        path = directory / "en.json"
    if path.exists():
        _translations = json.loads(path.read_text(encoding="utf-8"))
        _locale = locale
        logger.info("Loaded locale '%s' from %s", locale, path)
    else:
        logger.error("No locale files found in %s", directory)


def _resolve(key: str) -> Any:
    """Walk a dot-separated key through the nested translation dict."""
    value: Any = _translations
    for part in key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def t(key: str, **kwargs: Any) -> str:
    """Translate a key with optional interpolation.

    Supports ``{{var}}`` placeholders in translation strings.

    Args:
        key: Dot-separated translation key (e.g. ``"nav.home"``).
        **kwargs: Interpolation values.

    Returns:
        Translated string, or the key itself as fallback.
    """
    val = _resolve(key)

    if not isinstance(val, str):
        return key

    # Interpolation: replace {{var}} placeholders
    for k, v in kwargs.items():
        val = val.replace("{{" + k + "}}", str(v))

    return val


def get_locale() -> str:
    """Return the currently loaded locale code."""
    return _locale
