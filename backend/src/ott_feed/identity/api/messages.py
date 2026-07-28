"""Safe localized messages; keys never reveal account or credential state."""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    "ko": {
        "identity.request_accepted": "요청이 접수되었습니다.",
        "identity.authentication_failed": "로그인 정보를 확인할 수 없습니다.",
        "identity.session_expired": "세션이 만료되었습니다.",
        "identity.csrf_invalid": "요청을 확인할 수 없습니다.",
        "identity.try_again": "잠시 후 다시 시도해 주세요.",
        "identity.request_invalid": "요청 값을 확인해 주세요.",
        "identity.access_denied": "요청을 수행할 권한이 없습니다.",
    },
    "en": {
        "identity.request_accepted": "The request has been accepted.",
        "identity.authentication_failed": "The sign-in information could not be verified.",
        "identity.session_expired": "The session has expired.",
        "identity.csrf_invalid": "The request could not be verified.",
        "identity.try_again": "Please try again later.",
        "identity.request_invalid": "Please check the request values.",
        "identity.access_denied": "You do not have permission to perform this request.",
    },
}


def localize(message_key: str, accept_language: str | None) -> str:
    language = "en" if (accept_language or "").lower().startswith("en") else "ko"
    fallback = MESSAGES[language]["identity.request_invalid"]
    return MESSAGES[language].get(message_key, fallback)
