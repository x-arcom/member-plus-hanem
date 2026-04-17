# Bilingual Content Foundation

This module defines the rules and conventions for Arabic and English content.

## Rules

- All user-facing strings should have Arabic and English variants.
- If a translation is missing, the system should fallback to the default language.
- Use stable translation keys instead of hard-coded text.

## Example

```json
{
  "greeting": {
    "en": "Welcome",
    "ar": "مرحبا"
  }
}
```

## Phase 0 scope

- Define lookup conventions
- Document fallback behavior
- Prepare for integration with UI or messaging layers later
