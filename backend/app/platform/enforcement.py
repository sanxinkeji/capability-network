from app.auth.schemas import raise_auth_error
from app.platform.models import PlatformSettings

ERR_FEATURE_MARKETPLACE_DISABLED = 41020
ERR_FEATURE_MATCHING_DISABLED = 41021
ERR_FEATURE_WALLET_DISABLED = 41022
ERR_FEATURE_REFERRAL_DISABLED = 41023
ERR_FEATURE_AGENT_DISABLED = 41007


def require_marketplace_enabled(settings: PlatformSettings) -> None:
    if not settings.feature_marketplace_enabled:
        raise_auth_error(
            code=ERR_FEATURE_MARKETPLACE_DISABLED,
            message="marketplace is disabled",
            http_status=403,
        )


def require_matching_enabled(settings: PlatformSettings) -> None:
    if not settings.feature_matching_enabled:
        raise_auth_error(
            code=ERR_FEATURE_MATCHING_DISABLED,
            message="matching is disabled",
            http_status=403,
        )


def require_wallet_enabled(settings: PlatformSettings) -> None:
    if not settings.feature_wallet_enabled:
        raise_auth_error(
            code=ERR_FEATURE_WALLET_DISABLED,
            message="wallet is disabled",
            http_status=403,
        )


def require_referral_enabled(settings: PlatformSettings) -> None:
    if not settings.feature_referral_enabled:
        raise_auth_error(
            code=ERR_FEATURE_REFERRAL_DISABLED,
            message="referral is disabled",
            http_status=403,
        )


def require_agent_enabled(settings: PlatformSettings) -> None:
    if not settings.feature_agent_enabled:
        raise_auth_error(
            code=ERR_FEATURE_AGENT_DISABLED,
            message="agent access is disabled",
            http_status=403,
        )
