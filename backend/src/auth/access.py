"""
Dashboard access endpoint — PRD Appendix B.

GET /access?token={permanent_token}&goto={screen}

1. Look up token in merchants table.
2. If found: create HTTP session (cookie), redirect to dashboard (or goto screen).
3. If not found: show "Open from Salla" message.
"""
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from auth.session import create_session


router = APIRouter(tags=["access"])

# PRD Appendix B.3 — valid goto values
GOTO_MAP = {
    "overview": "/",
    "gift-config": "/gift-config",
    "members": "/members",
    "setup": "/setup",
    "analytics": "/analytics",
    "settings": "/settings",
    "promote": "/promote",
}

INVALID_TOKEN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>Member Plus</title>
<style>body{font-family:Tajawal,sans-serif;display:flex;justify-content:center;
align-items:center;min-height:100vh;background:#FAF8F4;color:#333;}
.card{background:#fff;border-radius:4px;padding:48px;max-width:420px;text-align:center;
box-shadow:0 2px 10px rgba(0,0,0,0.05);}
h1{color:#BE52EF;margin-bottom:16px;}
p{color:#666;line-height:1.6;}
</style></head>
<body>
<div class="card">
<h1>Member Plus</h1>
<p>هذا الرابط غير صالح أو منتهي الصلاحية.</p>
<p>يرجى فتح لوحة التحكم من داخل تطبيقات سلة.</p>
<hr style="margin:24px 0;border-color:#eee;">
<p>This link is invalid or expired.</p>
<p>Please open your dashboard from Salla → Apps → Member Plus.</p>
</div>
</body></html>
"""


@router.get("/access")
async def dashboard_access(
    request: Request,
    token: str = Query(...),
    goto: str = Query(default="overview"),
):
    """Exchange a permanent access token for an HTTP session cookie and
    redirect to the merchant dashboard."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.loader import load_config

    config = load_config()
    engine = create_engine(config.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Import whichever model version is active
        try:
            from database.models import Merchant
        except ImportError:
            from database.models import Merchant

        merchant = db.query(Merchant).filter(
            Merchant.permanent_access_token == token
        ).first()

        if not merchant:
            return HTMLResponse(INVALID_TOKEN_HTML, status_code=404)

        # Create session cookie on the redirect response
        target = GOTO_MAP.get(goto, "/")
        response = RedirectResponse(url=f"/dashboard{target}", status_code=302)
        create_session(response, merchant.id)
        return response

    finally:
        db.close()
