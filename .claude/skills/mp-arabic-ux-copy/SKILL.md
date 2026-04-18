---
name: mp-arabic-ux-copy
description: Review and improve Arabic UX copy across Member Plus screens — ensures clarity, consistency, proper Arabic grammar, luxury tone, and effective microcopy for Saudi merchant audience.
---

# Arabic UX Copy Review

## When to use
When reviewing or writing Arabic text for any Member Plus screen — labels, buttons, empty states, error messages, tooltips, insights, onboarding copy, or any merchant-facing text.

## Audience
Saudi merchants running e-commerce stores on Salla. Mix of tech-savvy and non-technical. Arabic-first but familiar with English tech terms. Expect professional, clear, trustworthy communication.

## Tone Guidelines
- **Professional but warm** — not corporate-cold, not casual-chatty
- **Confident** — "تم الحفظ" not "ربما تم الحفظ"
- **Action-oriented** — verbs first: "أنشئ هدية" not "إنشاء هدية جديدة"
- **Respectful** — use "أنت" form, never "أنتِ/أنتم"
- **Luxury-aligned** — elegant Arabic, avoid slang or colloquial
- **Concise** — every word earns its place

## Instructions

### 1) Check button labels
- Must clearly state the outcome: "حفظ التغييرات" not just "حفظ"
- Destructive actions need gravity: "إلغاء الاشتراك نهائياً" not "إلغاء"
- Primary vs secondary should be obvious from text weight
- No English unless it's a brand name (Salla, Member Plus)

### 2) Check status labels
Standardize across all screens:
- نشط (active) — green
- ملغى (cancelled) — gray
- منتهي (expired) — red
- مجدول (scheduled) — gold
- مسودة (draft) — muted

### 3) Check empty states
Every empty state needs:
- **What** — what would normally appear here
- **Why** — why it's empty (first time, no data, filter result)
- **What to do** — clear next action or guidance
- Example: "لا يوجد أعضاء بعد. شارك رابط العضوية مع عملائك للبدء."

### 4) Check error messages
- State what happened: "تعذّر حفظ التغييرات"
- State why if known: "تحقق من اتصالك بالإنترنت"
- State what to do: "أعد المحاولة" (with retry button)
- Never blame the user: "حدث خطأ" not "أدخلت بيانات خاطئة"

### 5) Check numbers and formatting
- Currency: always "ر.س" (never SAR, never ريال)
- Numbers: Arabic locale formatting via toLocaleString('ar-SA')
- Dates: Arabic month names or toLocaleDateString('ar-SA')
- Percentages: "١٥%" or "15%" — pick one and be consistent

### 6) Check terminology consistency
Key terms must be identical everywhere:
- الباقة الفضية / الباقة الذهبية (not فضي/ذهبي sometimes, فضية/ذهبية other times)
- الأعضاء (members) — never العملاء for subscribed members
- الهدية الشهرية (monthly gift) — never الكوبون or العرض
- الشحن المجاني (free shipping) — never شحن مجان
- إعدادات العضوية (membership settings) — never إعدادات الخطط
- سجل النشاط (activity log) — never السجل or الأحداث alone

### 7) Check insights and contextual copy
- Insights should feel smart, not generic
- Use concrete numbers: "وفّر أعضاؤك 1,425 ر.س" not "وفّر أعضاؤك مبلغاً"
- Reference time: "هذا الشهر" / "آخر 30 يوم" not just "مؤخراً"
- Comparisons help: "أعلى بـ 15% من الشهر الماضي"

### 8) Check Arabic grammar
- Dual form: "باقتان" (2 plans), "عضوان" (2 members)
- Plural rules: 3-10 use جمع (أعضاء), 11+ use مفرد (عضو)
- Gender agreement: "الباقة الذهبية" (feminine), "العضو النشط" (masculine)
- Avoid إعراب errors in labels and headings

## Output format
1. **Copy Inventory** — list all text on the screen with current wording
2. **Issues Found** — grouped by type (clarity, consistency, grammar, tone, missing)
3. **Suggested Rewrites** — current → suggested, with reason
4. **Missing Copy** — helper text, tooltips, or guidance that should exist
5. **Terminology Alignment** — any terms that differ from the standard glossary

## Rules
- Never suggest English replacements for Arabic labels
- Respect the luxury tone — no emoji in formal text (emojis are OK in nav icons)
- Keep labels under 4 words where possible
- Test that suggested text fits the UI container width
- Consider RTL text rendering and line breaks
