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
    const API_BASE = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
        ? 'http://localhost:8000'
        : location.origin;

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
            'ngrok-skip-browser-warning': '1',
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

    // ----- Reusable Pagination Component ----------------------------------
    MP.Paginator = function (opts) {
        const perPage = opts.perPage || 10;
        let currentPage = 1;
        let items = [];

        const self = {
            setItems(arr) { items = arr || []; currentPage = 1; },
            getPage() {
                const start = (currentPage - 1) * perPage;
                return items.slice(start, start + perPage);
            },
            totalPages() { return Math.max(1, Math.ceil(items.length / perPage)); },
            currentPage() { return currentPage; },
            total() { return items.length; },
            goTo(p) { currentPage = Math.max(1, Math.min(p, self.totalPages())); },

            render(containerEl) {
                const total = self.totalPages();
                if (total <= 1) { containerEl.innerHTML = ''; return; }

                let html = '';

                // Prev button
                html += `<button class="pg-btn${currentPage === 1 ? ' pg-btn--disabled' : ''}" data-pg="${currentPage - 1}" ${currentPage === 1 ? 'disabled' : ''}>‹</button>`;

                // Page numbers with ellipsis
                const pages = _pageRange(currentPage, total);
                pages.forEach(p => {
                    if (p === '...') {
                        html += '<span class="pg-dots">…</span>';
                    } else {
                        html += `<button class="pg-btn${p === currentPage ? ' pg-btn--active' : ''}" data-pg="${p}">${p}</button>`;
                    }
                });

                // Next button
                html += `<button class="pg-btn${currentPage === total ? ' pg-btn--disabled' : ''}" data-pg="${currentPage + 1}" ${currentPage === total ? 'disabled' : ''}>›</button>`;

                // Info
                const from = (currentPage - 1) * perPage + 1;
                const to = Math.min(currentPage * perPage, items.length);
                html += `<span class="pg-info">${from}–${to} من ${items.length}</span>`;

                containerEl.innerHTML = html;
                containerEl.querySelectorAll('[data-pg]').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const pg = Number(btn.dataset.pg);
                        if (pg >= 1 && pg <= total) {
                            self.goTo(pg);
                            if (opts.onChange) opts.onChange(self.getPage(), self.currentPage());
                            self.render(containerEl);
                        }
                    });
                });
            }
        };
        return self;
    };

    function _pageRange(current, total) {
        if (total <= 7) return Array.from({length: total}, (_, i) => i + 1);
        const pages = [];
        pages.push(1);
        if (current > 3) pages.push('...');
        for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i);
        if (current < total - 2) pages.push('...');
        pages.push(total);
        return pages;
    }

    window.MP = MP;
})();
