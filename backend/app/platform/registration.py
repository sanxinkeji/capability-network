import re

from app.platform.models import RegistrationMode

_VALID_MODES = {
    RegistrationMode.OPEN,
    RegistrationMode.INVITE_ONLY,
    RegistrationMode.CLOSED,
}


def normalize_registration_mode(mode: str | None) -> str:
    if mode in _VALID_MODES:
        return mode
    return RegistrationMode.OPEN


def registration_invite_required(settings) -> bool:
    mode = normalize_registration_mode(settings.registration_mode)
    if mode == RegistrationMode.INVITE_ONLY:
        return True
    return bool(getattr(settings, "registration_invite_required", False))


def parse_invite_codes(raw: str | None) -> set[str]:
    """Legacy text-list invite codes in platform_settings (deprecated)."""
    if not raw:
        return set()
    parts = re.split(r"[\n,;]+", raw)
    return {p.strip().upper() for p in parts if p.strip()}


def serialize_invite_codes(raw: str | None) -> str | None:
    codes = sorted(parse_invite_codes(raw))
    if not codes:
        return None
    return "\n".join(codes)
