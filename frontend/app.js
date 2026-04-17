/*
 * Member Plus — shared frontend utilities
 *
 * Exposes a single `MP` global with:
 *   - API base + api(path, opts) wrapper
 *   - auth (token read/redirect)
 *   - i18n helpers (getLang/setLang/applyDir)
 *   - toast(message, intent)
 *   - setLoading(button, on)
 */
(function () {
    const API_BASE = 'http://localhost:8000';

    const MP = {};

    // ----- Auth ---------------------------------------------------------
    MP.getToken = function () {
        const url = new URLSearchParams(location.search);
        const t = url.get('token') || localStorage.getItem('merchant_token');
        if (t) localStorage.setItem('merchant_token', t);
        return t;
    };

    MP.requireAuth = function () {
        const t = MP.getToken();
        if (!t) { window.location.href = 'index.html'; return null; }
        return t;
    };

    MP.logout = function () {
        localStorage.removeItem('merchant_token');
        window.location.href = 'index.html';
    };

    // ----- i18n ---------------------------------------------------------
    MP.getLang = function () {
        const url = new URLSearchParams(location.search);
        return url.get('lang') || localStorage.getItem('merchant_lang') || 'ar';
    };
    MP.setLang = function (lang) {
        localStorage.setItem('merchant_lang', lang);
        document.documentElement.lang = lang;
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    };

    // ----- API wrapper --------------------------------------------------
    class APIError extends Error {
        constructor(message, { status, code } = {}) {
            super(message);
            this.status = status;
            this.code = code;
        }
    }
    MP.APIError = APIError;

    MP.api = async function (path, opts = {}) {
        const token = MP.getToken();
        const headers = {
            'Accept': 'application/json',
            ...(opts.body ? { 'Content-Type': 'application/json' } : {}),
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...(opts.headers || {}),
        };
        let res;
        try {
            res = await fetch(API_BASE + path, { ...opts, headers });
        } catch (networkErr) {
            throw new APIError('network', { code: 'network' });
        }
        if (res.status === 204) return null;
        let body;
        try { body = await res.json(); } catch (_) { body = {}; }
        if (!res.ok) {
            const msg = body.detail || body.message || `HTTP ${res.status}`;
            if (res.status === 401) {
                // Surface once, then kick the user to login
                setTimeout(() => MP.logout(), 800);
                throw new APIError(msg, { status: 401, code: 'auth' });
            }
            throw new APIError(msg, { status: res.status });
        }
        return body;
    };

    // ----- Toast region -------------------------------------------------
    function ensureToastRegion() {
        let region = document.querySelector('.toast-region');
        if (!region) {
            region = document.createElement('div');
            region.className = 'toast-region';
            region.setAttribute('role', 'status');
            region.setAttribute('aria-live', 'polite');
            document.body.appendChild(region);
        }
        return region;
    }

    MP.toast = function (message, intent = 'info', { duration = 3500 } = {}) {
        const region = ensureToastRegion();
        const el = document.createElement('div');
        el.className = `toast toast--${intent}`;
        el.textContent = message;
        region.appendChild(el);
        setTimeout(() => {
            el.style.opacity = '0';
            el.style.transition = 'opacity 200ms';
            setTimeout(() => el.remove(), 220);
        }, duration);
    };

    // ----- Button loading helper ----------------------------------------
    MP.setLoading = function (btn, on) {
        if (!btn) return;
        if (on) {
            btn.dataset.loading = 'true';
            btn.setAttribute('aria-busy', 'true');
            btn.disabled = true;
        } else {
            delete btn.dataset.loading;
            btn.removeAttribute('aria-busy');
            btn.disabled = false;
        }
    };

    // ----- Human-friendly error messages -------------------------------
    MP.errorMessage = function (err, lang = 'ar') {
        if (err instanceof APIError) {
            if (err.code === 'network') {
                return lang === 'ar' ? 'تعذّر الاتصال بالخادم. تحقق من الإنترنت وحاول مجدداً.'
                                     : 'Could not reach the server. Check your connection and retry.';
            }
            if (err.status === 401) {
                return lang === 'ar' ? 'انتهت صلاحية الجلسة. جاري إعادة التوجيه لتسجيل الدخول.'
                                     : 'Session expired. Redirecting to login.';
            }
            if (err.status === 404) {
                return lang === 'ar' ? 'العنصر غير موجود.' : 'Not found.';
            }
            if (err.status === 409) {
                return lang === 'ar' ? 'العملية متعارضة مع الحالة الحالية: ' + err.message
                                     : 'Conflict with current state: ' + err.message;
            }
            return err.message;
        }
        return lang === 'ar' ? 'حدث خطأ غير متوقع.' : 'Something went wrong.';
    };

    window.MP = MP;
})();
