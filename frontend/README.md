# Member Plus Frontend (Phases 1 + 2)

HTML + JavaScript frontend for the Member Plus merchant experience, built on a
small shared design system defined by the skills in
[`../skills-main 3/.claude/skills/`](../skills-main%203/.claude/skills/).

## Files

| File | Role |
|------|------|
| `styles.css`     | Design system: tokens, components, states |
| `app.js`         | Shared JS: API wrapper, auth, toast, loading helpers, i18n |
| `index.html`     | Sign-in (Salla OAuth + demo) |
| `dashboard.html` | Merchant dashboard: trial hero, setup progress, subscription, profile, real metrics |
| `wizard.html`    | Phase 2 setup wizard (3 steps: store → first plan → launch) |
| `plans.html`     | Phase 2 subscription tiers + membership-plan management |
| `members.html`   | Phase 4 merchant-facing member list (filter / confirm / cancel) with shareable enrollment + member-lookup links |
| `customer.html`  | Phase 4 **public** enrollment page — `?store=<salla_store_id>` — Phase-R adds tier badges + benefit chips; **Phase G** adds coming-soon / already-member branches and an ROI calculator |
| `member.html`    | Phase R **public** member self-view — `?store=<salla_store_id>` — email-keyed lookup showing active subscription, benefit highlights, **Phase 6 coupon cards** (code + uses + expiry, copy button, mock-status hint), **Phase G** grace-period status, savings estimate, and renewal hint |

## Design System

Built against [`design-system-builder/SKILL.md`](../skills-main%203/.claude/skills/design-system-builder/SKILL.md).
All tokens live in `:root` CSS custom properties:

### Tokens

- **Color** — primitive layer (`--c-brand-500`, `--c-neutral-*`, `--c-success-*`, `--c-warning-*`, `--c-danger-*`, `--c-info-*`) + semantic layer (`--color-text-primary`, `--color-surface`, `--color-brand`, …)
- **Spacing** — 4-px base scale: `--space-1` … `--space-12`
- **Radius** — `--radius-sm` (4), `--radius-md` (8), `--radius-lg` (12), `--radius-pill`
- **Typography** — `--font-family`, `--font-size-{xs,sm,md,lg,xl,2xl,3xl}`, `--font-weight-{regular,medium,bold}`
- **Shadow / Motion** — `--shadow-{sm,md,lg}`, `--motion-{fast,default}` with a `prefers-reduced-motion` override

### Component groups

| Group        | Class(es)                                    | States covered |
|--------------|----------------------------------------------|----------------|
| Button       | `.btn`, `.btn--{primary,secondary,ghost,danger}`, `.btn--block`, `[data-loading]` | default, hover, active, focus-visible, disabled, **loading** |
| Card         | `.card`, `.card__header`, `.card__title`, `.card__grid` | — |
| Info box     | `.info-box`, `.info-box__{label,value}`      | — |
| Input        | `.input`, `.textarea`, `.select`, `.field`, `.field__error`, `.field[data-invalid]` | default, focus, **error**, disabled |
| Alert        | `.alert--{info,success,warning,danger}`      | intent variants |
| Pill         | `.pill--{neutral,success,warning,info,danger}` | status variants |
| Spinner      | `.spinner`, `.spinner--sm`                   | — |
| Skeleton     | `.skeleton--{line,block,stat}`               | **loading** placeholder |
| Empty state  | `.empty`, `.empty__{icon,title,body}`        | **empty** |
| Toast        | `.toast`, `.toast--{success,danger,warning}` | transient feedback |
| Progress     | `.progress`, `.progress__{fill,label}`       | — |
| Steps        | `.steps`, `.steps__bar[data-done]`           | wizard indicator |
| Table        | `.table`                                     | — |
| Hero         | `.hero`, `.hero__{title,value,label}`        | — |

### Four states on every data view

Every page that fetches data renders four distinct UI states — informed by
[`accessibility-review`](../skills-main%203/.claude/skills/accessibility-review/SKILL.md)
(feedback / state communication) and
[`heuristic-review`](../skills-main%203/.claude/skills/heuristic-review/SKILL.md)
(visibility of system status).

| Page              | Loading                    | Empty                             | Error                      | Data |
|-------------------|----------------------------|-----------------------------------|----------------------------|------|
| `dashboard.html`  | Skeleton cards             | n/a (always has trial + profile)  | `.empty` with retry + logout | Full dashboard |
| `wizard.html`     | Spinner + "Loading state…" | n/a                               | Inline `alert--danger`     | Step 1/2/3 form |
| `plans.html`      | Skeleton lines + tier spinner | `.empty` "No plans yet"        | `alert--danger` + retry    | Table + tier grid |
| `index.html`      | Button `data-loading`      | n/a                               | Inline `alert--danger`     | Login form |
| `members.html`    | Skeleton rows              | `.empty` "No members yet" + share-link hint | `.alert--danger` + retry | Filterable table + confirm/cancel |
| `customer.html`   | Skeleton plans grid        | `.empty` "No plans available"      | `.empty` with retry        | Plan selector + enroll form **and** success state after submit |
| `member.html`     | Skeleton hero + block      | `.empty` "No membership on this email" | `.empty` with retry     | Subscription hero + benefit-grid card |

### Accessibility

- `:focus-visible` ring on every interactive element (`--color-focus-ring`).
- Minimum 44-px touch target on buttons.
- All form inputs are `<label>`-bound; errors are `aria-describedby`-linked.
- Alerts use `role="alert"`, toasts use `role="status" aria-live="polite"`.
- Progress bars use `role="progressbar"` with `aria-valuenow`.
- Logical CSS properties (`inset-inline-end`, `border-inline-start`) serve both RTL and LTR from one stylesheet.
- `prefers-reduced-motion` disables animation.

### Bilingual

- `lang` query param (`?lang=ar` / `?lang=en`) + `merchant_lang` in localStorage.
- Every page has a `T` translation map; the lang toggle re-renders in-place.
- `document.dir` is set to `rtl` when `lang === 'ar'`, else `ltr`.

## Running locally

```bash
cd frontend
python3 -m http.server 3000
# open http://localhost:3000
```

Backend must be running at `http://localhost:8000`. See [`../backend/README.md`](../backend/README.md).

## API contracts used

See [`../backend/README.md`](../backend/README.md) for the full list. All calls
go through `MP.api(path, opts)` in `app.js`, which:

- attaches `Authorization: Bearer <token>` automatically,
- parses JSON errors into `MP.APIError { message, status, code }`,
- on 401, toasts then redirects to login,
- on network failure, surfaces a bilingual "connection" message.

## Adding a new page — checklist

When creating a new frontend page for any future phase, the following must be
in place before it's considered done (durable rule from project feedback):

- [ ] `<link rel="stylesheet" href="styles.css">` and `<script src="app.js">` only — no ad-hoc CSS duplication.
- [ ] Bilingual: `T.ar` + `T.en` objects, lang toggle button, `MP.setLang()` call.
- [ ] **Loading** state: skeleton or spinner, visible until fetch completes.
- [ ] **Empty** state: `.empty` card with title, body, and primary action.
- [ ] **Error** state: `alert--danger` (or `.empty` with retry) on fetch failure.
- [ ] **Success** state: real data rendered with proper pills / badges.
- [ ] Form validation: `field[data-invalid="true"]` per input + inline `field__error`.
- [ ] Destructive actions: use `confirm(...)` and `btn--danger`.
- [ ] Transient feedback: `MP.toast()` on create / update / delete.
- [ ] Every interactive element is keyboard-reachable with a visible focus ring.
