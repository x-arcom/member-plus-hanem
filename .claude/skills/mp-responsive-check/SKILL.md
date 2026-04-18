---
name: mp-responsive-check
description: Verify responsive behavior of any Member Plus screen across mobile (320-480px), tablet (481-860px), and desktop (861px+) — checks layout, touch targets, text overflow, sidebar behavior, and RTL rendering.
---

# Responsive Check

## When to use
When a screen needs to work on mobile devices. All Member Plus merchant screens are used by Saudi merchants who frequently check their dashboard on mobile phones.

## Breakpoints
- **Mobile:** 320-480px (iPhone SE to iPhone 15)
- **Tablet:** 481-860px (iPad mini, small tablets)
- **Desktop:** 861px+ (laptop/desktop with sidebar visible)
- **Sidebar collapse:** 860px (sidebar slides off, hamburger appears)

## Instructions

### 1) Check layout at each breakpoint
Read the HTML and inline/page styles. For each grid or flex layout, verify:
- `grid-template-columns` has a mobile fallback (1fr) or uses auto-fit/minmax
- `display: flex` with `gap` doesn't overflow on small screens
- `flex-wrap: wrap` is present where items might overflow
- Fixed widths don't exceed viewport

### 2) Check text overflow
- Long Arabic text in table cells, card titles, or labels
- Monospace codes (coupon codes, invoice refs) that might overflow
- Buttons with long Arabic labels that might wrap awkwardly
- Numbers that grow (1,425.50 ر.س takes more space than 0)

### 3) Check touch targets
- Minimum 44x44px for all tappable elements (buttons, links, icons)
- Adequate spacing between touch targets (no accidental taps)
- Filter dropdowns are finger-friendly
- Pagination buttons are large enough

### 4) Check the sidebar behavior
- At ≤860px: sidebar must be hidden (transform: translateX)
- Hamburger button must be visible
- Overlay must appear when sidebar opens
- Links must be tappable and properly spaced
- Sidebar must not cover critical content permanently

### 5) Check RTL-specific issues
- `inset-inline-end` not `right` for positioning
- `margin-inline-start` not `margin-left`
- `border-inline-start` not `border-left`
- `text-align: start` not `text-align: right`
- Flexbox with `row` direction flows correctly in RTL
- Icons/arrows that should flip in RTL

### 6) Check scroll behavior
- Horizontal scroll should NEVER appear (check for overflow-x)
- Tables wider than viewport need `overflow-x: auto` on wrapper
- Long stat grids need wrapping, not scrolling
- Charts must scale or simplify on mobile

### 7) Check the topbar
- Title truncation on small screens
- Action buttons (export, create) don't overflow
- Adequate padding on mobile (--space-3 minimum)

## Output format
For each issue:
```
**Breakpoint:** [mobile/tablet/desktop]
**Element:** [selector or description]
**Issue:** [what breaks]
**Fix:** [exact CSS with @media query]
```

End with a **Responsive Scorecard:**
- Mobile: ✅/⚠️/❌
- Tablet: ✅/⚠️/❌
- Desktop: ✅/⚠️/❌

## Rules
- Always provide fixes inside proper @media queries
- Test the narrowest case (320px iPhone SE)
- Check both portrait and landscape mental models
- Verify that `font-size` never goes below 12px on mobile
- Ensure summary/stat rows wrap to 2 columns on mobile (not 1 or 4)
