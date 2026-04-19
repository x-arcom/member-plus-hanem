"""
Member Plus — Notification Service

Handles all email notifications for merchants and members.
Uses branded HTML templates with #BE52EF purple brand color.

Production: SMTP via configured provider
Development: Mock (logs to console)
"""
import asyncio
import logging
import smtplib
from email.message import EmailMessage
from datetime import datetime
from typing import Optional
from config.loader import load_config

logger = logging.getLogger("notifications")

# ═══════════════════════════════════════════════════════════════
# Email Template System
# ═══════════════════════════════════════════════════════════════

BRAND_COLOR = "#BE52EF"
BRAND_DARK = "#9B35D4"
GOLD_COLOR = "#C9A84C"
BG_COLOR = "#FAF8F4"


def _base_template(content: str, direction: str = "rtl") -> str:
    """Wrap content in branded email shell."""
    return f"""<!DOCTYPE html>
<html dir="{direction}">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:{BG_COLOR};font-family:'IBM Plex Sans Arabic','Segoe UI',sans-serif;">
<div style="max-width:560px;margin:0 auto;padding:32px 16px;">
    <div style="text-align:center;margin-bottom:24px;">
        <span style="font-size:24px;">💎</span>
        <span style="font-size:16px;font-weight:600;color:{BRAND_COLOR};margin-inline-start:8px;">Member Plus</span>
    </div>
    <div style="background:#fff;border-radius:12px;padding:32px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">
        {content}
    </div>
    <div style="text-align:center;padding:20px;font-size:11px;color:#999;">
        Member Plus — نظام إدارة العضويات لمتاجر سلة
    </div>
</div>
</body></html>"""


def _cta_button(text: str, url: str) -> str:
    return f'<a href="{url}" style="display:inline-block;background:{BRAND_COLOR};color:#fff;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;margin-top:16px;">{text}</a>'


# ═══════════════════════════════════════════════════════════════
# Merchant Notification Templates
# ═══════════════════════════════════════════════════════════════

def welcome_merchant(store_name: str, dashboard_url: str, trial_days: int = 7) -> dict:
    """Sent when merchant installs the app."""
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">مرحباً بك في Member Plus! 🎉</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            تم تفعيل فترة تجربة مجانية لمدة <strong>{trial_days} أيام</strong> على متجرك <strong>{store_name}</strong>.
        </p>
        <p style="color:#555;line-height:1.7;margin-bottom:8px;">خلال الفترة التجريبية يمكنك:</p>
        <ul style="color:#555;line-height:2;padding-inline-start:20px;margin-bottom:20px;">
            <li>إعداد باقتي الفضية والذهبية</li>
            <li>تحديد الخصومات والشحن المجاني</li>
            <li>إطلاق برنامج العضوية لعملائك</li>
        </ul>
        <div style="background:{BG_COLOR};border:2px solid {BRAND_COLOR};border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;">
            <div style="font-size:13px;color:#555;margin-bottom:10px;">رابط لوحة التحكم — احفظ هذا الرابط</div>
            <a href="{dashboard_url}" style="font-size:14px;color:{BRAND_COLOR};font-weight:600;word-break:break-all;">{dashboard_url}</a>
        </div>
        <div style="text-align:center;">{_cta_button('الدخول للوحة التحكم', dashboard_url)}</div>
    """
    return {
        "subject": "مرحباً بك في Member Plus — ابدأ الآن",
        "html": _base_template(content),
        "type": "merchant.welcome",
    }


def trial_ending(store_name: str, days_left: int, dashboard_url: str) -> dict:
    """Sent 3 days and 1 day before trial ends."""
    urgency = "⚠️" if days_left <= 1 else "⏰"
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">{urgency} فترة التجربة تنتهي قريباً</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            تبقى <strong style="color:{BRAND_COLOR};">{days_left} {'يوم' if days_left > 1 else 'يوم واحد'}</strong> على انتهاء الفترة التجريبية لمتجر <strong>{store_name}</strong>.
        </p>
        <div style="background:#FFF8E1;border:1px solid {GOLD_COLOR};border-radius:8px;padding:16px;margin-bottom:16px;">
            <p style="color:#92400E;font-size:13px;margin:0;">بعد انتهاء التجربة، ستحتاج للاشتراك عبر متجر تطبيقات سلة لمواصلة استخدام البرنامج.</p>
        </div>
        <div style="text-align:center;">{_cta_button('إدارة الاشتراك', dashboard_url)}</div>
    """
    return {
        "subject": f"⏰ تبقى {days_left} يوم على انتهاء التجربة — {store_name}",
        "html": _base_template(content),
        "type": "merchant.trial_ending",
    }


def setup_complete(store_name: str, member_count: int, dashboard_url: str) -> dict:
    """Sent when merchant completes the setup wizard."""
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">تم إطلاق البرنامج بنجاح! 🚀</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            برنامج العضوية في <strong>{store_name}</strong> جاهز الآن. شارك رابط العضوية مع عملائك لبدء جذب الأعضاء.
        </p>
        <div style="text-align:center;">{_cta_button('الذهاب للوحة التحكم', dashboard_url)}</div>
    """
    return {
        "subject": f"🚀 برنامج العضوية جاهز — {store_name}",
        "html": _base_template(content),
        "type": "merchant.setup_complete",
    }


def new_member_joined(member_name: str, tier: str, price: str, dashboard_url: str) -> dict:
    """Sent to merchant when a new member subscribes."""
    tier_ar = "الذهبية" if tier == "gold" else "الفضية"
    tier_color = GOLD_COLOR if tier == "gold" else "#B0A898"
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">عضو جديد انضم! 🎉</h2>
        <div style="background:#f8f8f4;border-radius:8px;padding:16px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-weight:600;font-size:15px;">{member_name}</div>
                    <div style="font-size:12px;color:#888;margin-top:4px;">
                        <span style="background:rgba(201,168,76,0.12);color:{tier_color};padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600;">{tier_ar}</span>
                        · {price} ر.س/شهر
                    </div>
                </div>
            </div>
        </div>
        <div style="text-align:center;">{_cta_button('عرض التفاصيل', dashboard_url)}</div>
    """
    return {
        "subject": f"🎉 عضو جديد: {member_name} — الباقة {tier_ar}",
        "html": _base_template(content),
        "type": "merchant.new_member",
    }


def payment_failed(member_name: str, amount: str, dashboard_url: str) -> dict:
    """Sent to merchant when a member's payment fails."""
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#E53935;">❌ فشل دفع اشتراك</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            فشل تحصيل <strong>{amount} ر.س</strong> من العضو <strong>{member_name}</strong>.
        </p>
        <div style="background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;padding:16px;margin-bottom:16px;">
            <p style="color:#991B1B;font-size:13px;margin:0;">العضو سيبقى على عضويته حتى نهاية الفترة الحالية. إذا لم يتم الدفع، ستنتهي عضويته تلقائياً.</p>
        </div>
        <div style="text-align:center;">{_cta_button('متابعة الحالة', dashboard_url)}</div>
    """
    return {
        "subject": f"❌ فشل دفع: {member_name} — {amount} ر.س",
        "html": _base_template(content),
        "type": "merchant.payment_failed",
    }


def customer_interest(customer_name: str, store_name: str, interest_count: int, dashboard_url: str) -> dict:
    """Sent to merchant when a customer registers interest during trial/coming-soon."""
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">✨ عميل مهتم ببرنامج العضوية!</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            العميل <strong>{customer_name}</strong> سجّل اهتمامه ببرنامج العضوية في <strong>{store_name}</strong>.
        </p>
        <div style="background:#f8f8f4;border-radius:8px;padding:20px;text-align:center;margin-bottom:16px;">
            <div style="font-size:36px;font-weight:700;color:{BRAND_COLOR};">{interest_count}</div>
            <div style="font-size:13px;color:#888;margin-top:4px;">إجمالي العملاء المهتمين حتى الآن</div>
        </div>
        <div style="background:#ECFDF5;border:1px solid #A7F3D0;border-radius:8px;padding:16px;margin-bottom:16px;">
            <p style="color:#065F46;font-size:13px;margin:0;">عملاؤك ينتظرون! أكمل إعداد برنامج العضوية وأطلقه الآن لتحويل هذا الاهتمام إلى اشتراكات فعلية.</p>
        </div>
        <div style="text-align:center;">{_cta_button('إكمال الإعداد والإطلاق', dashboard_url)}</div>
    """
    return {
        "subject": f"✨ عميل جديد مهتم بالعضوية — الإجمالي {interest_count}",
        "html": _base_template(content),
        "type": "merchant.customer_interest",
    }


def monthly_report(store_name: str, stats: dict, dashboard_url: str) -> dict:
    """Monthly performance report sent on the 1st of each month."""
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">📊 التقرير الشهري — {store_name}</h2>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
            <div style="background:#f8f8f4;border-radius:8px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:700;color:{BRAND_COLOR};">{stats.get('member_count', 0)}</div>
                <div style="font-size:11px;color:#888;">أعضاء نشطين</div>
            </div>
            <div style="background:#f8f8f4;border-radius:8px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:700;color:#047857;">+{stats.get('revenue', 0)}</div>
                <div style="font-size:11px;color:#888;">إيراد الشهر (ر.س)</div>
            </div>
            <div style="background:#f8f8f4;border-radius:8px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:700;">{stats.get('new_members', 0)}</div>
                <div style="font-size:11px;color:#888;">أعضاء جدد</div>
            </div>
            <div style="background:#f8f8f4;border-radius:8px;padding:14px;text-align:center;">
                <div style="font-size:22px;font-weight:700;">{stats.get('churn_rate', 0)}%</div>
                <div style="font-size:11px;color:#888;">معدل التسرب</div>
            </div>
        </div>
        <div style="text-align:center;">{_cta_button('عرض التفاصيل الكاملة', dashboard_url)}</div>
    """
    return {
        "subject": f"📊 تقريرك الشهري — {store_name}",
        "html": _base_template(content),
        "type": "merchant.monthly_report",
    }


# ═══════════════════════════════════════════════════════════════
# Member Notification Templates (sent TO the customer)
# ═══════════════════════════════════════════════════════════════

def member_welcome(member_name: str, tier: str, store_name: str, dashboard_url: str) -> dict:
    """Sent to customer when they join a membership."""
    tier_ar = "الذهبية" if tier == "gold" else "الفضية"
    icon = "👑" if tier == "gold" else "💎"
    tier_gradient = "linear-gradient(135deg, #C9A84C, #E8D5A0)" if tier == "gold" else "linear-gradient(135deg, #B0A898, #D4CFC8)"
    content = f"""
        <div style="background:{tier_gradient};border-radius:10px;padding:24px;text-align:center;margin-bottom:20px;">
            <div style="font-size:40px;margin-bottom:8px;">{icon}</div>
            <div style="font-size:20px;font-weight:700;color:#1a1a1a;">الباقة {tier_ar}</div>
            <div style="font-size:13px;color:#1a1a1a;opacity:0.7;">عضوية نشطة</div>
        </div>
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">مرحباً بك {member_name}!</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            تم تفعيل عضويتك في <strong>الباقة {tier_ar}</strong> بمتجر <strong>{store_name}</strong>. مزاياك جاهزة للاستخدام الآن.
        </p>
        <p style="color:#555;line-height:1.7;margin-bottom:8px;font-weight:600;">مزاياك:</p>
        <ul style="color:#555;line-height:2;padding-inline-start:20px;margin-bottom:20px;">
            <li>خصم تلقائي على كل طلب</li>
            <li>شحن مجاني شهري</li>
            {'<li>هدية شهرية حصرية</li><li>وصول مبكر للمنتجات</li>' if tier == 'gold' else '<li>شارة العضوية المميزة</li>'}
        </ul>
        <div style="background:{BG_COLOR};border:2px solid {BRAND_COLOR};border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;">
            <div style="font-size:13px;color:#555;margin-bottom:10px;">لوحة عضويتك — احفظ هذا الرابط</div>
            <a href="{dashboard_url}" style="font-size:14px;color:{BRAND_COLOR};font-weight:600;word-break:break-all;">{dashboard_url}</a>
        </div>
        <div style="text-align:center;">{_cta_button('عرض عضويتي الآن', dashboard_url)}</div>
    """
    return {
        "subject": f"{icon} مرحباً بك في الباقة {tier_ar} — {store_name}",
        "html": _base_template(content),
        "type": "member.welcome",
    }


def member_gift_ready(member_name: str, gift_desc: str, code: str, expires: str, store_name: str) -> dict:
    """Sent to Gold member when their monthly gift is generated."""
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">🎁 هديتك الشهرية جاهزة!</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            أهلاً <strong>{member_name}</strong>! هدية هذا الشهر من <strong>{store_name}</strong> جاهزة لك:
        </p>
        <div style="background:{BG_COLOR};border-radius:8px;padding:16px;text-align:center;margin-bottom:16px;">
            <div style="font-size:14px;color:#555;margin-bottom:8px;">{gift_desc}</div>
            <div style="font-family:monospace;font-size:22px;font-weight:700;color:{BRAND_COLOR};letter-spacing:0.05em;background:#fff;padding:12px;border-radius:8px;border:2px dashed {BRAND_COLOR};">
                {code}
            </div>
            <div style="font-size:11px;color:#999;margin-top:8px;">ينتهي {expires} · استخدام واحد فقط</div>
        </div>
    """
    return {
        "subject": f"🎁 هديتك الشهرية جاهزة — {store_name}",
        "html": _base_template(content),
        "type": "member.gift_ready",
    }


def member_renewal_reminder(member_name: str, tier: str, price: str, renewal_date: str, store_name: str) -> dict:
    """Sent 3 days before renewal."""
    tier_ar = "الذهبية" if tier == "gold" else "الفضية"
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">🔄 تجديد العضوية قريباً</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            أهلاً <strong>{member_name}</strong>! سيتم تجديد عضويتك في الباقة <strong>{tier_ar}</strong> بتاريخ <strong>{renewal_date}</strong>.
        </p>
        <div style="background:#f8f8f4;border-radius:8px;padding:16px;margin-bottom:16px;">
            <div style="display:flex;justify-content:space-between;">
                <span style="color:#888;">المبلغ</span>
                <span style="font-weight:600;">{price} ر.س</span>
            </div>
        </div>
        <p style="color:#888;font-size:12px;">سيتم الخصم تلقائياً من طريقة الدفع المسجلة في سلة.</p>
    """
    return {
        "subject": f"🔄 تجديد العضوية — {renewal_date}",
        "html": _base_template(content),
        "type": "member.renewal_reminder",
    }


def member_payment_failed(member_name: str, amount: str, store_name: str) -> dict:
    """Sent to member when their payment fails."""
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#E53935;">❌ فشل تجديد العضوية</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            أهلاً <strong>{member_name}</strong>! لم نتمكن من تحصيل <strong>{amount} ر.س</strong> لتجديد عضويتك في <strong>{store_name}</strong>.
        </p>
        <div style="background:#FEF2F2;border:1px solid #FCA5A5;border-radius:8px;padding:16px;margin-bottom:16px;">
            <p style="color:#991B1B;font-size:13px;margin:0;">يرجى تحديث طريقة الدفع في حسابك على سلة خلال الأيام القادمة للحفاظ على مزايا عضويتك.</p>
        </div>
    """
    return {
        "subject": f"❌ فشل تجديد عضويتك — {store_name}",
        "html": _base_template(content),
        "type": "member.payment_failed",
    }


def member_cancelled(member_name: str, tier: str, end_date: str, total_saved: str, store_name: str) -> dict:
    """Sent to member when they cancel."""
    tier_ar = "الذهبية" if tier == "gold" else "الفضية"
    content = f"""
        <h2 style="font-size:22px;margin-bottom:12px;color:#1a1a1a;">تم إلغاء العضوية</h2>
        <p style="color:#555;line-height:1.7;margin-bottom:16px;">
            أهلاً <strong>{member_name}</strong>! تم إلغاء عضويتك في الباقة <strong>{tier_ar}</strong>.
        </p>
        <div style="background:#f8f8f4;border-radius:8px;padding:16px;margin-bottom:16px;">
            <p style="margin:0 0 8px;color:#555;">مزاياك ستبقى نشطة حتى <strong>{end_date}</strong></p>
            <p style="margin:0;color:{BRAND_COLOR};font-weight:600;">وفّرت خلال عضويتك: {total_saved} ر.س</p>
        </div>
        <p style="color:#888;font-size:13px;">يمكنك إعادة الاشتراك في أي وقت من صفحة العضوية في المتجر.</p>
    """
    return {
        "subject": f"تم إلغاء عضويتك — {store_name}",
        "html": _base_template(content),
        "type": "member.cancelled",
    }


# ═══════════════════════════════════════════════════════════════
# Delivery System
# ═══════════════════════════════════════════════════════════════

def build_message(subject: str, html_body: str, recipient: str, sender: str) -> EmailMessage:
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content('This email requires an HTML-capable email client.')
    msg.add_alternative(html_body, subtype='html')
    return msg


def send_email_sync(message: EmailMessage, config) -> bool:
    smtp_cls = smtplib.SMTP_SSL if config.email_use_ssl else smtplib.SMTP
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


async def deliver(notification: dict, recipient_email: str, merchant_id: Optional[str] = None, member_id: Optional[str] = None) -> bool:
    """Send a notification and log it."""
    config = load_config()
    sender = config.email_from or "Member Plus <no-reply@memberplus.com>"
    message = build_message(notification["subject"], notification["html"], recipient_email, sender)

    success = False
    if config.email_host and config.email_port:
        try:
            success = await asyncio.to_thread(send_email_sync, message, config)
        except Exception as exc:
            logger.warning("SMTP failed for %s: %s — using mock", recipient_email, exc)

    if not success:
        logger.info("EMAIL (mock) → %s | %s | %s", recipient_email, notification["type"], notification["subject"])
        success = True

    # Log to email_log table
    try:
        from database.models import EmailLog
        from database.init_db import get_session
        db = get_session()
        try:
            db.add(EmailLog(
                merchant_id=merchant_id or "",
                member_id=member_id,
                email_type=notification["type"],
                recipient_email=recipient_email,
                language="ar",
                subject=notification["subject"],
                status="sent" if success else "failed",
            ))
            db.commit()
        finally:
            db.close()
    except Exception:
        pass  # Don't fail the notification if logging fails

    return success


# ═══════════════════════════════════════════════════════════════
# Convenience functions (backward compat)
# ═══════════════════════════════════════════════════════════════

async def send_welcome_email(merchant_name: str, merchant_email: str, language: str = "ar") -> bool:
    notif = welcome_merchant(merchant_name, "https://app.memberplus.sa/dashboard")
    return await deliver(notif, merchant_email)


async def send_trial_expiring_email(merchant_email: str, days_remaining: int, language: str = "ar") -> bool:
    notif = trial_ending("", days_remaining, "https://app.memberplus.sa/settings#billing")
    return await deliver(notif, merchant_email)


async def send_setup_complete_email(merchant_email: str, language: str = "ar") -> bool:
    notif = setup_complete("", 0, "https://app.memberplus.sa/dashboard")
    return await deliver(notif, merchant_email)
