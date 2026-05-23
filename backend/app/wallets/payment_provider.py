from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlencode
from uuid import UUID, uuid4

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DepositOrderResult:
    provider: str
    provider_ref: str
    amount_cents: int
    status: str  # pending | paid
    pay_url: str | None = None


@dataclass
class PaymentNotifyResult:
    provider_ref: str
    amount_cents: int
    status: str  # paid | failed


class PaymentProvider(ABC):
    @abstractmethod
    async def create_deposit(
        self,
        *,
        user_id: UUID,
        order_id: UUID,
        amount_cents: int,
        currency: str = "CNY",
    ) -> DepositOrderResult:
        """创建充值支付单。"""

    @abstractmethod
    async def verify_notify(self, *, payload: bytes, headers: dict[str, str]) -> PaymentNotifyResult | None:
        """验签并解析支付回调。"""


class PaymentProviderError(RuntimeError):
    pass


@dataclass
class PlatformPaymentConfig:
    payment_alipay_source: str = "direct"
    payment_wechat_source: str = "direct"
    payment_product_name_prefix: str | None = None
    payment_product_name_suffix: str | None = None
    easypay_pid: str | None = None
    easypay_key: str | None = None
    easypay_api_base: str | None = None
    easypay_alipay_type: str | None = None
    easypay_wechat_type: str | None = None
    stripe_enabled: bool = False
    stripe_public_key: str | None = None
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None


def _easypay_sign(params: dict[str, str], key: str) -> str:
    filtered = {k: v for k, v in params.items() if v != "" and k not in ("sign", "sign_type")}
    ordered = "&".join(f"{k}={filtered[k]}" for k in sorted(filtered))
    return hashlib.md5(f"{ordered}{key}".encode()).hexdigest()


class EasyPayProvider(PaymentProvider):
    """EasyPay 协议聚合支付（兼容多数第三方易支付平台）。"""

    def __init__(self, *, config: PlatformPaymentConfig, channel: str):
        self.config = config
        self.channel = channel.lower()
        if not (config.easypay_pid and config.easypay_key and config.easypay_api_base):
            raise PaymentProviderError("EasyPay 未配置，请在运营后台填写 PID / 密钥 / API 地址")

    def _pay_type(self) -> str:
        if self.channel == "alipay":
            return self.config.easypay_alipay_type or "alipay"
        if self.channel == "wechat":
            return self.config.easypay_wechat_type or "wxpay"
        raise PaymentProviderError(f"EasyPay 不支持渠道: {self.channel}")

    def _product_name(self) -> str:
        parts = [
            self.config.payment_product_name_prefix or "",
            "钱包充值",
            self.config.payment_product_name_suffix or "",
        ]
        name = "".join(p for p in parts if p).strip()
        return name or "Capability 钱包充值"

    async def create_deposit(
        self,
        *,
        user_id: UUID,
        order_id: UUID,
        amount_cents: int,
        currency: str = "CNY",
    ) -> DepositOrderResult:
        if currency != "CNY":
            raise PaymentProviderError("EasyPay 仅支持 CNY")

        provider_ref = f"cn_ep_{order_id.hex[:24]}"
        notify_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/wallets/payment-notify/easypay"
        return_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/app/wallet"
        params = {
            "pid": self.config.easypay_pid or "",
            "type": self._pay_type(),
            "out_trade_no": provider_ref,
            "notify_url": notify_url,
            "return_url": return_url,
            "name": self._product_name(),
            "money": f"{amount_cents / 100:.2f}",
            "sitename": "Capability",
        }
        params["sign"] = _easypay_sign(params, self.config.easypay_key or "")
        params["sign_type"] = "MD5"

        api_base = (self.config.easypay_api_base or "").rstrip("/")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{api_base}/mapi.php", data=params)

        try:
            data = resp.json()
        except json.JSONDecodeError:
            logger.error("easypay create failed: %s", resp.text)
            raise PaymentProviderError("EasyPay 下单失败：响应格式错误")

        if str(data.get("code")) not in ("1", "200"):
            raise PaymentProviderError(data.get("msg") or "EasyPay 下单失败")

        pay_url = data.get("qrcode") or data.get("payurl") or data.get("url")
        if not pay_url:
            raise PaymentProviderError("EasyPay 未返回支付链接")

        return DepositOrderResult(
            provider="easypay",
            provider_ref=provider_ref,
            amount_cents=amount_cents,
            status="pending",
            pay_url=pay_url,
        )

    async def verify_notify(self, *, payload: bytes, headers: dict[str, str]) -> PaymentNotifyResult | None:
        text = payload.decode(errors="ignore")
        if text.startswith("{"):
            try:
                flat = {k: str(v) for k, v in json.loads(text).items()}
            except json.JSONDecodeError:
                return None
        else:
            parsed = parse_qs(text)
            flat = {k: v[0] for k, v in parsed.items()}

        sign = flat.pop("sign", "")
        flat.pop("sign_type", None)
        expected = _easypay_sign(flat, self.config.easypay_key or "")
        if sign.lower() != expected.lower():
            logger.warning("easypay notify signature invalid")
            return None

        if flat.get("trade_status") not in ("TRADE_SUCCESS", "success", "1"):
            return PaymentNotifyResult(
                provider_ref=flat.get("out_trade_no", ""),
                amount_cents=int(float(flat.get("money", "0")) * 100),
                status="failed",
            )

        return PaymentNotifyResult(
            provider_ref=flat.get("out_trade_no", ""),
            amount_cents=int(float(flat.get("money", "0")) * 100),
            status="paid",
        )


class StripeProvider(PaymentProvider):
    """Stripe Checkout（国际支付，需配置 stripe 密钥）。"""

    def __init__(self, *, config: PlatformPaymentConfig):
        self.config = config
        if not (config.stripe_secret_key and config.stripe_public_key):
            raise PaymentProviderError("Stripe 未配置，请在运营后台填写公钥与私钥")

    def _verify_webhook_signature(self, *, payload: bytes, sig_header: str) -> bool:
        secret = self.config.stripe_webhook_secret
        if not secret:
            logger.warning("stripe webhook secret not configured")
            return False
        if not sig_header:
            return False

        parts: dict[str, list[str]] = {}
        for item in sig_header.split(","):
            if "=" not in item:
                continue
            key, value = item.split("=", 1)
            parts.setdefault(key.strip(), []).append(value.strip())

        timestamp = parts.get("t", [None])[0]
        signatures = parts.get("v1", [])
        if not timestamp or not signatures:
            return False

        try:
            if abs(int(time.time()) - int(timestamp)) > 300:
                logger.warning("stripe webhook timestamp outside tolerance")
                return False
        except ValueError:
            return False

        signed_payload = f"{timestamp}.{payload.decode()}"
        expected = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return any(hmac.compare_digest(expected, signature) for signature in signatures)

    async def create_deposit(
        self,
        *,
        user_id: UUID,
        order_id: UUID,
        amount_cents: int,
        currency: str = "CNY",
    ) -> DepositOrderResult:
        provider_ref = f"cn_st_{order_id.hex[:24]}"
        notify_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/wallets/payment-notify/stripe"
        stripe_currency = "cny" if currency.upper() == "CNY" else currency.lower()
        form = urlencode(
            {
                "mode": "payment",
                "success_url": f"{settings.PUBLIC_BASE_URL.rstrip('/')}/app/wallet?paid=1",
                "cancel_url": f"{settings.PUBLIC_BASE_URL.rstrip('/')}/app/wallet",
                "client_reference_id": provider_ref,
                "line_items[0][price_data][currency]": stripe_currency,
                "line_items[0][price_data][product_data][name]": "Capability Wallet Top-up",
                "line_items[0][price_data][unit_amount]": str(amount_cents),
                "line_items[0][quantity]": "1",
                "metadata[out_trade_no]": provider_ref,
            }
        )
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                content=form,
                headers={
                    "Authorization": f"Bearer {self.config.stripe_secret_key}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
        if resp.status_code >= 400:
            logger.error("stripe checkout failed: %s", resp.text)
            raise PaymentProviderError("Stripe 创建支付会话失败")
        data = resp.json()
        pay_url = data.get("url")
        if not pay_url:
            raise PaymentProviderError("Stripe 未返回支付链接")
        return DepositOrderResult(
            provider="stripe",
            provider_ref=provider_ref,
            amount_cents=amount_cents,
            status="pending",
            pay_url=pay_url,
        )

    async def verify_notify(self, *, payload: bytes, headers: dict[str, str]) -> PaymentNotifyResult | None:
        sig_header = headers.get("stripe-signature") or headers.get("Stripe-Signature") or ""
        if not self._verify_webhook_signature(payload=payload, sig_header=sig_header):
            logger.warning("stripe notify signature invalid")
            return None

        try:
            event = json.loads(payload.decode())
        except json.JSONDecodeError:
            return None
        obj = event.get("data", {}).get("object", {})
        if event.get("type") != "checkout.session.completed":
            return None
        provider_ref = obj.get("client_reference_id") or obj.get("metadata", {}).get("out_trade_no", "")
        amount_cents = int(obj.get("amount_total") or 0)
        if not provider_ref:
            return None
        return PaymentNotifyResult(provider_ref=provider_ref, amount_cents=amount_cents, status="paid")


def _read_pem(path: str) -> bytes:
    pem_path = Path(path)
    if not pem_path.is_file():
        raise PaymentProviderError(f"密钥文件不存在: {path}")
    return pem_path.read_bytes()


def _wechat_authorization(*, method: str, url_path: str, body: str) -> str:
    private_key = serialization.load_pem_private_key(
        _read_pem(settings.WECHAT_PAY_PRIVATE_KEY_PATH),
        password=None,
    )
    timestamp = str(int(time.time()))
    nonce = uuid4().hex
    message = f"{method}\n{url_path}\n{timestamp}\n{nonce}\n{body}\n"
    signature = private_key.sign(message.encode(), padding.PKCS1v15(), hashes.SHA256())
    sig_b64 = base64.b64encode(signature).decode()
    return (
        f'WECHATPAY2-SHA256-RSA2048 mchid="{settings.WECHAT_PAY_MCH_ID}",'
        f'nonce_str="{nonce}",signature="{sig_b64}",timestamp="{timestamp}",'
        f'serial_no="{settings.WECHAT_PAY_CERT_SERIAL}"'
    )


class WechatPayProvider(PaymentProvider):
    async def create_deposit(
        self,
        *,
        user_id: UUID,
        order_id: UUID,
        amount_cents: int,
        currency: str = "CNY",
    ) -> DepositOrderResult:
        if not settings.wechat_pay_configured:
            raise PaymentProviderError(
                "微信支付未配置，请设置 WECHAT_PAY_APP_ID / WECHAT_PAY_MCH_ID / "
                "WECHAT_PAY_API_V3_KEY / WECHAT_PAY_CERT_SERIAL / WECHAT_PAY_PRIVATE_KEY_PATH"
            )
        if currency != "CNY":
            raise PaymentProviderError("微信支付仅支持 CNY")

        provider_ref = f"cn_wx_{order_id.hex[:24]}"
        notify_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/wallets/payment-notify/wechat"
        body_obj = {
            "appid": settings.WECHAT_PAY_APP_ID,
            "mchid": settings.WECHAT_PAY_MCH_ID,
            "description": "Capability 钱包充值",
            "out_trade_no": provider_ref,
            "notify_url": notify_url,
            "amount": {"total": amount_cents, "currency": "CNY"},
        }
        body = json.dumps(body_obj, ensure_ascii=False)
        url_path = "/v3/pay/transactions/native"
        auth = _wechat_authorization(method="POST", url_path=url_path, body=body)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"https://api.mch.weixin.qq.com{url_path}",
                content=body.encode(),
                headers={
                    "Authorization": auth,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
        if resp.status_code >= 400:
            logger.error("wechat native pay failed: %s %s", resp.status_code, resp.text)
            raise PaymentProviderError(f"微信支付下单失败: {resp.text}")

        data = resp.json()
        code_url = data.get("code_url")
        if not code_url:
            raise PaymentProviderError("微信支付未返回 code_url")

        return DepositOrderResult(
            provider="wechat",
            provider_ref=provider_ref,
            amount_cents=amount_cents,
            status="pending",
            pay_url=code_url,
        )

    async def verify_notify(self, *, payload: bytes, headers: dict[str, str]) -> PaymentNotifyResult | None:
        if not settings.WECHAT_PAY_API_V3_KEY:
            raise PaymentProviderError("微信支付回调验签未配置")

        try:
            body = json.loads(payload.decode())
        except json.JSONDecodeError:
            return None

        resource = body.get("resource") or {}
        if resource.get("algorithm") != "AEAD_AES_256_GCM":
            return None

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        nonce = resource.get("nonce", "")
        ciphertext = resource.get("ciphertext", "")
        associated_data = resource.get("associated_data", "")
        if not nonce or not ciphertext:
            return None

        aesgcm = AESGCM(settings.WECHAT_PAY_API_V3_KEY.encode())
        plain = aesgcm.decrypt(
            nonce.encode(),
            base64.b64decode(ciphertext),
            associated_data.encode() if associated_data else None,
        )
        trade = json.loads(plain.decode())
        if trade.get("trade_state") != "SUCCESS":
            return PaymentNotifyResult(
                provider_ref=trade.get("out_trade_no", ""),
                amount_cents=int(trade.get("amount", {}).get("total", 0)),
                status="failed",
            )

        return PaymentNotifyResult(
            provider_ref=trade.get("out_trade_no", ""),
            amount_cents=int(trade.get("amount", {}).get("total", 0)),
            status="paid",
        )


def _alipay_sign(params: dict[str, str]) -> str:
    private_key = serialization.load_pem_private_key(
        _read_pem(settings.ALIPAY_PRIVATE_KEY_PATH),
        password=None,
    )
    ordered = "&".join(f"{k}={params[k]}" for k in sorted(params) if params[k] != "" and k != "sign")
    signature = private_key.sign(ordered.encode(), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(signature).decode()


class AlipayProvider(PaymentProvider):
    async def create_deposit(
        self,
        *,
        user_id: UUID,
        order_id: UUID,
        amount_cents: int,
        currency: str = "CNY",
    ) -> DepositOrderResult:
        if not settings.alipay_configured:
            raise PaymentProviderError(
                "支付宝未配置，请设置 ALIPAY_APP_ID / ALIPAY_PRIVATE_KEY_PATH / ALIPAY_PUBLIC_KEY_PATH"
            )
        if currency != "CNY":
            raise PaymentProviderError("支付宝仅支持 CNY")

        provider_ref = f"cn_ali_{order_id.hex[:24]}"
        notify_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/wallets/payment-notify/alipay"
        biz_content = json.dumps(
            {
                "out_trade_no": provider_ref,
                "total_amount": f"{amount_cents / 100:.2f}",
                "subject": "Capability 钱包充值",
            },
            ensure_ascii=False,
        )
        params = {
            "app_id": settings.ALIPAY_APP_ID,
            "method": "alipay.trade.precreate",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": notify_url,
            "biz_content": biz_content,
        }
        params["sign"] = _alipay_sign(params)
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(settings.ALIPAY_GATEWAY, data=params)
        data = resp.json()
        response = data.get("alipay_trade_precreate_response") or {}
        if response.get("code") != "10000":
            logger.error("alipay precreate failed: %s", response)
            raise PaymentProviderError(response.get("sub_msg") or response.get("msg") or "支付宝下单失败")

        qr_code = response.get("qr_code")
        if not qr_code:
            raise PaymentProviderError("支付宝未返回 qr_code")

        return DepositOrderResult(
            provider="alipay",
            provider_ref=provider_ref,
            amount_cents=amount_cents,
            status="pending",
            pay_url=qr_code,
        )

    async def verify_notify(self, *, payload: bytes, headers: dict[str, str]) -> PaymentNotifyResult | None:
        from urllib.parse import parse_qs

        parsed = parse_qs(payload.decode())
        flat = {k: v[0] for k, v in parsed.items()}
        if flat.get("trade_status") not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            return PaymentNotifyResult(
                provider_ref=flat.get("out_trade_no", ""),
                amount_cents=int(float(flat.get("total_amount", "0")) * 100),
                status="failed",
            )

        public_key = serialization.load_pem_public_key(_read_pem(settings.ALIPAY_PUBLIC_KEY_PATH))
        sign = flat.pop("sign", "")
        flat.pop("sign_type", None)
        ordered = "&".join(f"{k}={flat[k]}" for k in sorted(flat) if flat[k] != "")
        try:
            public_key.verify(
                base64.b64decode(sign),
                ordered.encode(),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except Exception:
            logger.warning("alipay notify signature invalid")
            return None

        return PaymentNotifyResult(
            provider_ref=flat.get("out_trade_no", ""),
            amount_cents=int(float(flat.get("total_amount", "0")) * 100),
            status="paid",
        )


class TestInstantPaymentProvider(PaymentProvider):
    """仅用于 pytest（PAYMENT_PROVIDER=test）。"""

    async def create_deposit(
        self,
        *,
        user_id: UUID,
        order_id: UUID,
        amount_cents: int,
        currency: str = "CNY",
    ) -> DepositOrderResult:
        return DepositOrderResult(
            provider="test",
            provider_ref=f"test_{order_id.hex[:16]}",
            amount_cents=amount_cents,
            status="paid",
            pay_url=None,
        )

    async def verify_notify(self, *, payload: bytes, headers: dict[str, str]) -> PaymentNotifyResult | None:
        return None


def get_payment_provider(
    channel: str | None = None,
    *,
    config: PlatformPaymentConfig | None = None,
) -> PaymentProvider:
    if settings.PAYMENT_PROVIDER.lower() == "test":
        return TestInstantPaymentProvider()

    provider = (channel or settings.PAYMENT_PROVIDER).lower()
    cfg = config or PlatformPaymentConfig()

    if provider == "stripe":
        return StripeProvider(config=cfg)

    if provider == "wechat":
        if cfg.payment_wechat_source == "easypay":
            return EasyPayProvider(config=cfg, channel="wechat")
        return WechatPayProvider()

    if provider == "alipay":
        if cfg.payment_alipay_source == "easypay":
            return EasyPayProvider(config=cfg, channel="alipay")
        return AlipayProvider()

    if provider == "easypay":
        return EasyPayProvider(config=cfg, channel="alipay")

    if provider == "test":
        return TestInstantPaymentProvider()
    raise PaymentProviderError(f"不支持的支付渠道: {provider}")


def platform_payment_config_from_row(row) -> PlatformPaymentConfig:
    return PlatformPaymentConfig(
        payment_alipay_source=getattr(row, "payment_alipay_source", "direct") or "direct",
        payment_wechat_source=getattr(row, "payment_wechat_source", "direct") or "direct",
        payment_product_name_prefix=getattr(row, "payment_product_name_prefix", None),
        payment_product_name_suffix=getattr(row, "payment_product_name_suffix", None),
        easypay_pid=getattr(row, "easypay_pid", None),
        easypay_key=getattr(row, "easypay_key", None),
        easypay_api_base=getattr(row, "easypay_api_base", None),
        easypay_alipay_type=getattr(row, "easypay_alipay_type", None),
        easypay_wechat_type=getattr(row, "easypay_wechat_type", None),
        stripe_enabled=getattr(row, "stripe_enabled", False),
        stripe_public_key=getattr(row, "stripe_public_key", None),
        stripe_secret_key=getattr(row, "stripe_secret_key", None),
        stripe_webhook_secret=getattr(row, "stripe_webhook_secret", None),
    )
