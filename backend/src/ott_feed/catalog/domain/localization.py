"""Locale selection that always reports the locale actually served."""

from __future__ import annotations

from dataclasses import dataclass

from ott_feed.catalog.domain.errors import CatalogError
from ott_feed.catalog.domain.models import Localization


@dataclass(frozen=True, slots=True)
class LocalizedValue:
    value: Localization
    requested_locale: str
    actual_locale: str
    fallback: bool


def select_localization(
    values: dict[str, Localization], requested: str, fallback: str
) -> LocalizedValue:
    if requested in values:
        return LocalizedValue(values[requested], requested, requested, False)
    language = requested.split("-", 1)[0].lower()
    for locale in sorted(values):
        if locale.split("-", 1)[0].lower() == language:
            return LocalizedValue(values[locale], requested, locale, True)
    if fallback in values:
        return LocalizedValue(values[fallback], requested, fallback, True)
    if values:
        actual = sorted(values)[0]
        return LocalizedValue(values[actual], requested, actual, True)
    raise CatalogError("LOC_NOT_FOUND", "no approved localization is available")
