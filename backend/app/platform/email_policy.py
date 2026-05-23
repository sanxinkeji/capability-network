import re

from app.auth.schemas import raise_auth_error

ERR_EMAIL_DOMAIN_NOT_ALLOWED = 40310


def parse_registration_email_domains(raw: str | None) -> set[str]:
    if not raw or not raw.strip():
        return set()
    parts = re.split(r"[\n,;]+", raw)
    domains: set[str] = set()
    for part in parts:
        domain = part.strip().lower()
        if domain.startswith("@"):
            domain = domain[1:]
        if domain:
            domains.add(domain)
    return domains


def assert_email_domain_allowed(email: str, domains_raw: str | None) -> None:
    allowed = parse_registration_email_domains(domains_raw)
    if not allowed:
        return
    local, _, domain = email.lower().partition("@")
    if not local or not domain or domain not in allowed:
        raise_auth_error(
            code=ERR_EMAIL_DOMAIN_NOT_ALLOWED,
            message="email domain is not allowed for registration",
            http_status=403,
        )
