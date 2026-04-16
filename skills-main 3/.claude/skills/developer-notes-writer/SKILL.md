---
name: developer-notes-writer
description: Write clear, practical developer notes for a feature, flow, or component by summarizing behavior, rules, states, validations, dependencies, and important implementation considerations in a way that supports smoother handoff and execution.
---

# Developer Notes Writer Skill

## When to use this skill
Use this skill when the user provides:
- a feature description
- a requirement
- a user flow
- a component behavior summary
- business rules
- acceptance criteria
- product notes
- a PRD section
- handoff context
- implementation notes draft

Use this skill when the goal is to:
- prepare clear notes for developers
- support product-to-engineering handoff
- explain behavior and implementation expectations
- highlight important rules and constraints
- reduce ambiguity before development starts
- make execution easier and more aligned

## Goal
The goal of this skill is to turn product or design logic into concise, practical developer notes that make implementation easier to understand and less error-prone.

This skill should help:
- summarize what the feature does
- clarify important logic and behavior
- highlight validations, restrictions, and conditions
- surface states and transitions that matter for implementation
- point out dependencies or assumptions
- reduce misunderstanding between product, design, and engineering
- support cleaner and more confident implementation

## Input type
The user may provide:
- a feature description
- a requirement
- a flow
- a component behavior summary
- scenarios
- acceptance criteria
- product notes
- design notes
- raw handoff notes
- screenshots described in text

The input may be complete or partial.

## Instructions
When using this skill, analyze the feature or behavior carefully, then convert it into developer-facing notes.

### 1) Understand the feature first
Determine:
- what the feature does
- who the main actor is
- what the intended outcome is
- whether the behavior depends on state, permissions, validations, or external conditions

### 2) Summarize the feature clearly
Start with a short and practical summary of what needs to be built or supported.

### 3) Clarify the important behavior
Explain the expected behavior in implementation-oriented language, such as:
- when the action is available
- when it is blocked
- what happens on success
- what happens on failure
- what should remain unchanged
- what depends on status, permissions, or data completeness

### 4) Highlight validations and restrictions
Clearly mention:
- required data
- invalid input handling
- disabled conditions
- state restrictions
- permission restrictions
- business rules that affect implementation

### 5) Mention important states
Call out any key states relevant to development, such as:
- default
- loading
- disabled
- validation
- success
- error
- empty
- pending
- completed
- blocked
- exhausted

### 6) Mention dependencies or assumptions
If the behavior depends on:
- API response
- backend support
- quota logic
- campaign state
- user role
- feature flags
- external integrations

mention that clearly.

### 7) Mention what should not happen
Important developer notes often include non-behavior as well.
Clearly mention:
- what should remain unchanged
- what should not be triggered
- what should not be counted, consumed, or recorded
- what should not affect another part of the system

### 8) Mention implementation-sensitive details
Call out areas that developers should pay extra attention to, such as:
- edge-case handling
- state preservation
- timing-sensitive behavior
- race conditions if relevant
- UI feedback expectations
- backend/frontend coordination points

### 9) Mention unclear points
If some logic is still not fully defined, list the unclear areas separately instead of hiding them.

### 10) Keep the result concise and useful
The output should be practical, readable, and useful during implementation.
Do not turn it into a full PRD or long essay.

## Output format
Always structure the response like this:

1. Feature Summary  
A short explanation of what this feature or behavior is meant to do.

2. Core Behavior  
The main expected behavior developers should implement.

3. Validations and Restrictions  
The rules, blocking conditions, and validations that matter.

4. Important States  
The key states that should be handled.

5. What Must Not Happen  
The behaviors or side effects that must be avoided.

6. Dependencies and Assumptions  
Anything that depends on backend logic, other states, roles, or unresolved assumptions.

7. Developer Notes  
Direct implementation-oriented notes the team should pay attention to.

8. Open Questions  
Anything that still needs clarification before implementation.

## Tone
The tone should be:
- clear
- practical
- concise
- implementation-aware
- product-aware
- direct

## Rules
- Do not rewrite the entire requirement unnecessarily.
- Do not invent unsupported technical details.
- If something is inferred, explicitly label it as inferred.
- Focus on developer usefulness, not presentation fluff.
- Keep the notes actionable and implementation-oriented.
- Do not turn the response into test cases.
- Do not hide unclear logic; list it clearly.
- Make the result useful for real handoff and execution.

## What good output looks like
A strong response should help the user:
- communicate requirements more clearly to developers
- reduce ambiguity during implementation
- avoid missed rules or side effects
- highlight important states and conditions
- improve alignment between product, design, and engineering