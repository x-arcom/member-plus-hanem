---
name: mp-screen-audit
description: Run a full UX audit on any Member Plus screen — checks heuristics, visual hierarchy, interaction patterns, data presentation, and merchant workflow against the PRD and luxury brand standards.
---

# Member Plus Screen Audit

## When to use
When reviewing any merchant dashboard screen (dashboard, plans, promotions, members, activity, settings) or customer-facing page (member.html, customer.html) for UX quality.

## Context
Member Plus is a Salla Partner App enabling Saudi merchants to run paid membership programs (Silver/Gold tiers). The dashboard is Arabic-first (RTL), luxury-positioned (NET-A-PORTER / AMEX level), using #BE52EF purple brand, Cormorant Garamond display + IBM Plex Sans Arabic UI fonts, warm cream (#FAF8F4) background.

## Instructions

### 1) Read the target screen HTML file completely
Understand every element, state, and interaction on the page.

### 2) Check against Nielsen's 10 heuristics
For each heuristic, identify specific issues on THIS screen:
- **Visibility of system status** — loading states, feedback after actions, progress indicators
- **Match between system and real world** — Arabic terminology correctness, mental model alignment
- **User control and freedom** — undo, cancel, back navigation, escape hatches
- **Consistency** — with other Member Plus screens (sidebar, tokens, patterns)
- **Error prevention** — validation, confirmation for destructive actions, input constraints
- **Recognition over recall** — labels, tooltips, contextual help
- **Flexibility** — search, filters, keyboard shortcuts, bulk actions
- **Minimalist design** — information density, visual noise, hierarchy clarity
- **Error recovery** — error messages, retry mechanisms, fallback states
- **Help and guidance** — onboarding hints, helper text, empty state guidance

### 3) Check luxury brand alignment
- Does it feel premium or generic?
- Is Cormorant Garamond used for headings/display numbers?
- Is spacing generous enough (luxury = breathing room)?
- Are shadows layered for depth?
- Are transitions smooth and subtle?
- Are colors on-brand (#BE52EF purple, #C9A84C gold, brand silver)?

### 4) Check the 4 required states
Every data-driven section must have:
- **Loading** — skeleton or spinner
- **Empty** — guidance + CTA
- **Error** — message + retry
- **Success/Data** — the actual content

### 5) Check data presentation
- Are numbers formatted consistently (Arabic numerals, ر.س currency)?
- Are dates formatted in Arabic locale?
- Are charts/visualizations clear and purposeful?
- Is there appropriate context for metrics (trends, comparisons)?

### 6) Check merchant workflow
- Can the merchant accomplish their primary task in ≤3 clicks?
- Is the information hierarchy correct (most important → least)?
- Are CTAs clear and action-oriented?
- Does the page connect logically to related pages?

## Output format
1. **Screen Summary** — what it does, who uses it
2. **What Works Well** — strengths (be specific)
3. **Critical Issues** — must-fix before launch (with exact element references)
4. **Improvement Opportunities** — nice-to-haves with specific CSS/HTML suggestions
5. **Brand Alignment Score** — 1-10 with reasoning
6. **State Coverage** — which of the 4 states are present/missing
7. **Priority Action List** — top 5 fixes in order of impact

## Rules
- Reference specific HTML elements, CSS classes, and line numbers
- Give exact code fixes, not vague advice
- Compare against other Member Plus screens for consistency
- Consider mobile (< 480px) and tablet (480-860px) breakpoints
- Flag any hardcoded values that should use design tokens
