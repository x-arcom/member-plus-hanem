---
name: mp-accessibility
description: Review any Member Plus screen for accessibility — checks ARIA labels, keyboard navigation, color contrast, focus management, screen reader support, and RTL-specific a11y concerns.
---

# Accessibility Review

## When to use
When verifying a screen meets WCAG 2.1 AA standards. Member Plus serves Saudi merchants who may use screen readers, keyboard navigation, or have visual impairments.

## Instructions

### 1) Check semantic HTML
- Headings: proper h1 → h6 hierarchy (one h1 per page)
- Landmarks: `<main>`, `<nav>`, `<aside>`, `<header>` used correctly
- Lists: `<ul>/<li>` for navigation, not bare `<div>` chains
- Buttons vs links: `<button>` for actions, `<a>` for navigation
- Tables: `<th>` for headers, `scope` attribute where needed

### 2) Check ARIA attributes
- `aria-current="page"` on active sidebar link ✓
- `aria-label` on icon-only buttons (hamburger, close, etc.)
- `aria-hidden="true"` on decorative emoji/icons
- `role="status"` on toast region
- `aria-live="polite"` on dynamic content areas
- `aria-pressed` on toggle buttons
- `aria-expanded` on collapsible sections

### 3) Check keyboard navigation
- Tab order follows visual order (RTL: right to left, top to bottom)
- All interactive elements are focusable
- Focus is visible (outline or ring on :focus-visible)
- Escape closes modals/overlays
- Enter/Space activates buttons
- Arrow keys work in dropdown menus

### 4) Check color contrast
- Text on background: minimum 4.5:1 ratio (AA)
- Large text (18px+ or 14px bold+): minimum 3:1 ratio
- Check these specific combinations:
  - White text on #BE52EF purple → verify ratio
  - Gray text on #FAF8F4 cream → verify ratio
  - Gold (#C9A84C) text on white → might fail
  - Silver (#6B6560) text on white → verify ratio
  - Success green on green background → verify
  - Muted text (rgba(0,0,0,0.5)) on cream → verify

### 5) Check focus management
- After modal opens: focus moves to modal
- After modal closes: focus returns to trigger element
- After delete/action: focus moves to next logical element
- Page load: focus is at top (no random auto-focus)
- Detail panel open: focus moves to panel

### 6) Check images and icons
- `<img>` tags have `alt` attribute
- Decorative images: `alt=""`
- SVG icons: `aria-hidden="true"` if decorative
- Emoji in nav: wrapped with `aria-hidden` or labeled

### 7) Check forms
- Every `<input>` has a visible `<label>` (not just placeholder)
- Required fields marked with `required` attribute
- Error messages linked via `aria-describedby`
- Form groups wrapped in `<fieldset>` with `<legend>`

### 8) Check RTL-specific a11y
- `dir="rtl"` on `<html>` ✓
- `lang="ar"` on `<html>` ✓
- Logical properties used (inline-start/end, not left/right)
- Text alignment uses `start`/`end`, not `left`/`right`
- Number inputs: inputmode="numeric" for mobile keyboards

### 9) Check dynamic content
- Content loaded via JS: announced to screen readers
- Toast notifications: in `aria-live` region
- Loading states: `aria-busy="true"` on container
- Error states: announced when they appear

### 10) Check touch and pointer
- Touch targets: minimum 44x44px
- No hover-only interactions (mobile has no hover)
- Drag interactions have keyboard alternatives

## Output format
| Category | Status | Issues |
|----------|--------|--------|
| Semantic HTML | ✅/⚠️/❌ | details |
| ARIA | ✅/⚠️/❌ | details |
| Keyboard | ✅/⚠️/❌ | details |
| Color Contrast | ✅/⚠️/❌ | details |
| Focus Management | ✅/⚠️/❌ | details |
| Forms | ✅/⚠️/❌ | details |
| RTL | ✅/⚠️/❌ | details |
| Dynamic Content | ✅/⚠️/❌ | details |

Then list priority fixes with exact HTML/CSS code.

## Rules
- Don't flag issues that don't affect real users
- Prioritize: screen reader → keyboard → contrast → nice-to-haves
- Give exact `aria-*` attributes to add, not just "add ARIA"
- Check the actual HTML, not assumptions
- Consider Saudi Arabic screen reader behavior (NVDA/JAWS with Arabic)
