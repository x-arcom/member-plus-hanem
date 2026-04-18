---
name: mp-luxury-polish
description: Elevate any Member Plus screen from functional to luxury-grade — refine typography, spacing, shadows, micro-interactions, color usage, and visual hierarchy to match NET-A-PORTER / AMEX membership standards.
---

# Luxury Polish Skill

## When to use
When a screen is functionally complete but needs visual refinement to match the luxury brand standard. Use after the screen works correctly — this skill focuses purely on visual and interaction quality.

## Brand Reference
- **Inspiration:** NET-A-PORTER membership, AMEX Centurion communications, Gulf luxury e-commerce
- **Colors:** #BE52EF (purple primary), #C9A84C (gold), #B0A898 → #6B6560 (silver), #FAF8F4 (cream bg), #0E0E0E (near-black)
- **Fonts:** Cormorant Garamond (display/numbers), IBM Plex Sans Arabic (UI)
- **Radius:** 2px buttons, 4px cards (precision, not playful)
- **Shadows:** Layered (xs → sm → md → lg), purple glow for branded elements
- **Motion:** 120ms fast, 200ms default, ease-out curves

## Instructions

### 1) Typography audit
- Headings MUST use Cormorant Garamond (`--font-display`)
- Large numbers/KPIs MUST use Cormorant Garamond
- Body/UI text uses IBM Plex Sans Arabic (`--font-family`)
- Labels should be 11px minimum (not 10px)
- Letter-spacing: tight (-0.01em) for display, wide (0.08em) for uppercase labels
- Line-height: 1.25 tight for headings, 1.5-1.7 for body text

### 2) Spacing audit
- Section spacing: minimum 32px (--space-8) between major blocks
- Card padding: minimum 24px (--space-6) for hero cards
- Breathing room: luxury = generous whitespace, never cramped
- Container padding: 32px vertical, 24px horizontal minimum

### 3) Shadow and depth
- Cards at rest: --shadow-sm (subtle)
- Cards on hover: --shadow-card-hover + translateY(-1px or -2px)
- Elevated elements (modals, dropdowns): --shadow-lg
- Branded elements: --shadow-purple for purple-tinted glow
- Never flat — every card should have at least --shadow-xs

### 4) Color refinement
- Purple (#BE52EF) for primary actions, active states, brand accents
- Gold (#C9A84C) for Gold tier, warnings, premium indicators
- Silver (#6B6560 text, rgba(176,168,152,0.15) bg) for Silver tier
- Success: soft green (--c-success-50 bg, --c-success-700 text)
- Never use raw hex — always reference CSS custom properties
- Backgrounds should be warm (#FAF8F4), not cold white

### 5) Micro-interactions
- All interactive elements need transition (border-color, box-shadow, transform)
- Hover: subtle border color change + shadow elevation
- Active/pressed: scale(0.97) or darker background
- Focus: visible outline or ring (accessibility)
- Loading: skeleton shimmer or spinner with brand purple
- Success feedback: toast with slide-in animation

### 6) Visual hierarchy
- ONE primary element per section (the most important thing should be obvious)
- KPI values: largest, boldest, brand-colored
- Labels: smallest, muted, uppercase with letter-spacing
- Actions: clearly differentiated (primary = filled purple, secondary = outlined, ghost = text-only)
- Destructive actions: red border/text, never filled red button

### 7) Consistency check
- Same patterns across all 6+ pages
- Same card style, same shadow, same radius
- Same status pill colors (active=green, cancelled=gray, expired=red)
- Same tier badge colors (gold=warm, silver=cool gray)
- Same date format, currency format, number format

## Output format
For each issue found, provide:
```
**Element:** [specific selector or description]
**Issue:** [what's wrong]
**Fix:** [exact CSS or HTML change]
**Impact:** [high/medium/low]
```

End with a **Before/After Summary** describing the overall visual improvement.

## Rules
- Give EXACT CSS code, not descriptions
- Reference design tokens (--space-X, --font-size-X, --shadow-X)
- Check both desktop and mobile rendering
- Don't over-design — luxury is restraint, not decoration
- Less is more: remove visual noise before adding embellishment
