---
name: mp-state-coverage
description: Verify that every data-driven section on a Member Plus screen has all 4 required states (loading, empty, error, success) with proper transitions, feedback, and merchant guidance.
---

# State Coverage Check

## When to use
When verifying that a screen handles all edge cases. Per Member Plus project rules, EVERY screen that fetches data must implement 4 states.

## The 4 Required States

### 1) Loading State
- Must show immediately when page loads or data refreshes
- Use skeleton loaders (not spinners) for content areas
- Skeleton shape should approximate the final content layout
- Must be visible for at least 200ms (no flash)
- Check: `id="state-loading"` exists and shows skeletons

### 2) Empty State
- Shows when API returns successfully but with zero items
- Must include: icon (48px, 0.35 opacity), title (display font), description, CTA
- Description should tell the merchant what to do next
- CTA should link to the action that creates the first item
- Check: `id="state-empty"` exists with `.empty` class

### 3) Error State
- Shows when API call fails (network error, 500, timeout)
- Must include: warning icon, title, error message, retry button
- Error message should be human-readable Arabic (via `MP.errorMessage()`)
- Retry button should call the `load()` function
- Must NOT show raw error codes or stack traces
- Check: `id="state-error"` exists with retry button wired

### 4) Data/Success State
- Shows when API returns data successfully
- All data rendered from API response (not hardcoded)
- Mock data acceptable for demo but clearly marked
- Check: `id="state-data"` exists

## Instructions

### 1) Read the HTML file
Find all state containers (`state-loading`, `state-empty`, `state-error`, `state-data`).

### 2) Check the show() function
Verify it toggles all states correctly:
```js
function show(w) {
    ['state-loading','state-error','state-empty','state-data'].forEach(id => {
        document.getElementById(id).hidden = id !== w;
    });
}
```

### 3) Check the load() function
Verify the flow:
- `show('state-loading')` at start
- API call in try/catch
- Empty check: if no data → `show('state-empty')`
- Success: render data → `show('state-data')`
- Catch: set error message → `show('state-error')`

### 4) Check sub-sections
Some pages have inline loading within sections (e.g., member detail panel). These also need loading/error states.

### 5) Check action feedback
- Save/create buttons: should show loading state on button (`MP.setLoading`)
- Success: toast notification
- Error: toast with error message
- Button should be disabled during loading (prevent double-submit)

### 6) Check filter/search states
When filters return zero results, show inline empty (not full-page empty):
- "لا توجد نتائج" with the current filter context
- Option to clear filters

## Output format
| Section | Loading | Empty | Error | Data | Notes |
|---------|---------|-------|-------|------|-------|
| Main page | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | details |
| Sub-section | ✅/❌ | ✅/❌ | ✅/❌ | ✅/❌ | details |

Then list specific fixes needed with exact code.

## Rules
- Every `MP.api()` call MUST be in try/catch
- Loading state must show BEFORE the API call, not after
- Error messages must use `MP.errorMessage(err, 'ar')`
- Empty state must be genuinely reachable (not hidden behind mock data)
- Mock data for demo is fine but real empty state must still work
