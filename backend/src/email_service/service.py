"""
Email service for merchant notifications.

Phase 1 MVP: Mock email (logs to console)
Phase 1 Full: Integrate SMTP as a real email provider.
"""

import asyncio
import smtplib
from email.message import EmailMessage
from datetime import datetime
from config.loader import load_config


class EmailTemplates:
    """Email templates in Arabic and English."""
    
    WELCOME_EMAIL_AR = """
    <html>
    <body style="font-family: Arial, sans-serif; direction: rtl;">
        <h2>مرحباً بك في Member Plus! 🎉</h2>
        <p>شكراً لتثبيت تطبيق Member Plus على متجرك!</p>
        
        <p>تم تفعيل فترة تجربة لمدة <strong>14 يوم</strong>. خلال هذه الفترة يمكنك:</p>
        <ul>
            <li>إعداد برنامج العضوية</li>
            <li>إنشاء خطط العضوية</li>
            <li>اختبار التجربة الكاملة</li>
        </ul>
        
        <p><a href="http://localhost:3000/dashboard" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">الذهاب إلى لوحة التحكم</a></p>
        
        <p>للمساعدة: support@memberplus.com</p>
    </body>
    </html>
    """
    
    WELCOME_EMAIL_EN = """
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Welcome to Member Plus! 🎉</h2>
        <p>Thank you for installing Member Plus on your store!</p>
        
        <p>Your <strong>14-day trial</strong> is now active. During this time you can:</p>
        <ul>
            <li>Set up your membership program</li>
            <li>Create membership plans</li>
            <li>Test the complete experience</li>
        </ul>
        
        <p><a href="http://localhost:3000/dashboard" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a></p>
        
        <p>Questions? support@memberplus.com</p>
    </body>
    </html>
    """


def build_message(subject: str, html_body: str, recipient: str, sender: str) -> EmailMessage:
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content('This email requires an HTML-capable email client.')
    msg.add_alternative(html_body, subtype='html')
    return msg


def send_email_sync(message: EmailMessage, config) -> bool:
    if config.email_use_ssl:
        smtp_cls = smtplib.SMTP_SSL
    else:
        smtp_cls = smtplib.SMTP

    server = smtp_cls(config.email_host, config.email_port or 0, timeout=20)
    try:
        if config.email_use_tls and not config.email_use_ssl:
            server.starttls()
        if config.email_user and config.email_password:
            server.login(config.email_user, config.email_password)
        server.send_message(message)
        return True
    finally:
        server.quit()


async def send_welcome_email(merchant_name: str, merchant_email: str, language: str = "ar") -> bool:
    """
    Send welcome email to merchant.

    If SMTP settings are configured, this sends via SMTP. Otherwise it falls back to a mock log.
    """
    config = load_config()
    template = EmailTemplates.WELCOME_EMAIL_AR if language == "ar" else EmailTemplates.WELCOME_EMAIL_EN
    subject = "مرحباً بك في Member Plus" if language == "ar" else "Welcome to Member Plus!"
    sender = config.email_from or f"Member Plus <no-reply@memberplus.com>"

    message = build_message(subject, template, merchant_email, sender)

    if config.email_host and config.email_port:
        try:
            return await asyncio.to_thread(send_email_sync, message, config)
        except Exception as exc:
            print(f"❌ SMTP send failed, falling back to mock: {exc}")

    print(f"""
    ✉️  EMAIL SENT (Mock)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    To: {merchant_email}
    Subject: {subject}
    Language: {language}
    Timestamp: {datetime.utcnow().isoformat()}
    Template: {len(template)} bytes
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    return True


_TRIAL_EXPIRING_AR = """
<html><body style="font-family: Arial; direction: rtl;">
    <h2>فترة التجربة على وشك الانتهاء</h2>
    <p>تبقى <strong>{days}</strong> أيام على انتهاء فترة التجربة.</p>
    <p>لمتابعة استخدام Member Plus بعد انتهاء الفترة، يرجى اختيار الباقة المناسبة:</p>
    <p><a href="http://localhost:3000/plans.html#billing"
          style="background:#667eea; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
          عرض الباقات
       </a></p>
</body></html>
"""

_TRIAL_EXPIRING_EN = """
<html><body style="font-family: Arial;">
    <h2>Your Member Plus trial is ending soon</h2>
    <p>You have <strong>{days}</strong> days left on your trial.</p>
    <p>Pick a subscription tier to keep your membership program running:</p>
    <p><a href="http://localhost:3000/plans.html#billing"
          style="background:#667eea; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
          View tiers
       </a></p>
</body></html>
"""

_SETUP_COMPLETE_AR = """
<html><body style="font-family: Arial; direction: rtl;">
    <h2>تم إكمال الإعداد! 🎉</h2>
    <p>برنامج العضوية جاهز. يمكنك الآن إدارة الخطط ومتابعة الأعضاء من لوحة التحكم.</p>
    <p><a href="http://localhost:3000/dashboard.html"
          style="background:#667eea; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
          الذهاب للوحة التحكم
       </a></p>
</body></html>
"""

_SETUP_COMPLETE_EN = """
<html><body style="font-family: Arial;">
    <h2>Setup complete! 🎉</h2>
    <p>Your membership program is live. Manage plans and members from the dashboard.</p>
    <p><a href="http://localhost:3000/dashboard.html"
          style="background:#667eea; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
          Go to dashboard
       </a></p>
</body></html>
"""


async def _deliver(subject: str, html: str, recipient: str) -> bool:
    config = load_config()
    sender = config.email_from or "Member Plus <no-reply@memberplus.com>"
    message = build_message(subject, html, recipient, sender)
    if config.email_host and config.email_port:
        try:
            return await asyncio.to_thread(send_email_sync, message, config)
        except Exception as exc:
            print(f"❌ SMTP send failed, falling back to mock: {exc}")
    print(f"""
    ✉️  EMAIL SENT (Mock)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    To: {recipient}
    Subject: {subject}
    Timestamp: {datetime.utcnow().isoformat()}
    Body: {len(html)} bytes
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)
    return True


async def send_trial_expiring_email(merchant_email: str, days_remaining: int, language: str = "ar") -> bool:
    """Sent when a merchant's trial drops below a threshold (e.g. 3 days)."""
    html = (_TRIAL_EXPIRING_AR if language == "ar" else _TRIAL_EXPIRING_EN).format(days=days_remaining)
    subject = "فترة التجربة على وشك الانتهاء" if language == "ar" else "Your Member Plus trial is ending soon"
    return await _deliver(subject, html, merchant_email)


async def send_setup_complete_email(merchant_email: str, language: str = "ar") -> bool:
    """Sent once `setup_state` reaches `setup_complete`."""
    html = _SETUP_COMPLETE_AR if language == "ar" else _SETUP_COMPLETE_EN
    subject = "تم إكمال الإعداد" if language == "ar" else "Setup complete"
    return await _deliver(subject, html, merchant_email)
