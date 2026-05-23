import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.platform.models import PlatformSettings

logger = logging.getLogger(__name__)

DEFAULT_VERIFY_SUBJECT = "邮箱验证码"
DEFAULT_VERIFY_HTML = """<!DOCTYPE html>
<html><body>
<p>{{name}}，您好：</p>
<p>您的验证码为：<strong>{{code}}</strong></p>
<p>验证码 15 分钟内有效，请勿泄露。</p>
</body></html>"""


def _render_template(template: str, *, name: str, code: str) -> str:
    return template.replace("{{name}}", name).replace("{{code}}", code)


def smtp_configured(settings: PlatformSettings) -> bool:
    return bool(settings.smtp_host and settings.smtp_from)


def send_verification_email(
    settings: PlatformSettings,
    *,
    to_email: str,
    display_name: str,
    code: str,
) -> None:
    subject = settings.email_template_verify_subject or DEFAULT_VERIFY_SUBJECT
    html_template = settings.email_template_verify_html or DEFAULT_VERIFY_HTML
    html_body = _render_template(html_template, name=display_name, code=code)

    if not smtp_configured(settings):
        logger.info(
            "email verification (mock/log mode): to=%s code=%s smtp_not_configured",
            to_email,
            code,
        )
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.smtp_from or ""
    message["To"] = to_email
    message.attach(MIMEText(re.sub(r"<[^>]+>", "", html_body), "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user and settings.smtp_password:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.sendmail(settings.smtp_from or "", [to_email], message.as_string())
        logger.info("verification email sent to %s", to_email)
    except Exception:
        logger.warning(
            "verification email send failed for %s, code=%s (logged for recovery)",
            to_email,
            code,
            exc_info=True,
        )
