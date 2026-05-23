from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_JWT_SECRET_KEY = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "capability-network-backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/capability_network"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET_KEY: str = DEFAULT_JWT_SECRET_KEY
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # API 安全：限流与登录锁定（依赖 REDIS_URL）
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN_MAX: int = 10
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60
    RATE_LIMIT_REGISTER_MAX: int = 5
    RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = 3600
    RATE_LIMIT_PAYMENT_NOTIFY_MAX: int = 100
    RATE_LIMIT_PAYMENT_NOTIFY_WINDOW_SECONDS: int = 60
    RATE_LIMIT_API_KEY_ISSUE_MAX: int = 10
    RATE_LIMIT_API_KEY_ISSUE_WINDOW_SECONDS: int = 3600
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 900
    LOGIN_LOCKOUT_SCOPE: str = "account"  # account | ip | both

    CORS_ORIGINS: str = "http://localhost:5173"

    # 支付与提现（生产必填）
    PAYMENT_PROVIDER: str = "wechat"  # wechat | alipay | test（仅 pytest）
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"
    MIN_DEPOSIT_CENTS: int = 100
    MIN_WITHDRAW_CENTS: int = 10000
    MAX_WITHDRAW_CENTS: int = 50_000_000
    PAYMENT_ORDER_EXPIRE_MINUTES: int = 30

    # 微信支付 v3
    WECHAT_PAY_APP_ID: str = ""
    WECHAT_PAY_MCH_ID: str = ""
    WECHAT_PAY_API_V3_KEY: str = ""
    WECHAT_PAY_CERT_SERIAL: str = ""
    WECHAT_PAY_PRIVATE_KEY_PATH: str = ""

    # 支付宝
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY_PATH: str = ""
    ALIPAY_PUBLIC_KEY_PATH: str = ""
    ALIPAY_GATEWAY: str = "https://openapi.alipay.com/gateway.do"

    # 数据库备份（pg_dump 输出目录；dry-run 跳过实际 dump/上传）
    BACKUP_DIR: str = ""
    BACKUP_DRY_RUN: bool = False

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def wechat_pay_configured(self) -> bool:
        return bool(
            self.WECHAT_PAY_APP_ID
            and self.WECHAT_PAY_MCH_ID
            and self.WECHAT_PAY_API_V3_KEY
            and self.WECHAT_PAY_CERT_SERIAL
            and self.WECHAT_PAY_PRIVATE_KEY_PATH
        )

    @property
    def alipay_configured(self) -> bool:
        return bool(
            self.ALIPAY_APP_ID
            and self.ALIPAY_PRIVATE_KEY_PATH
            and self.ALIPAY_PUBLIC_KEY_PATH
        )


settings = Settings()
