---
name: design-system-review
description: Review an existing design system or UI kit to uncover gaps, inconsistencies, structural issues, weaknesses in foundations, components, states, or naming, and suggest practical improvements that make the system clearer and more scalable.
---

# Design System Review Skill

## When to use this skill
Use this skill when the user provides:
- an existing design system
- a UI kit
- foundations
- tokens
- a component list
- a naming structure
- system documentation
- a description of the current design system
- a summary of a component library or interface system

Use this skill when the goal is to:
- evaluate the strength of the current design system
- uncover gaps, duplication, or inconsistency
- review foundations
- review component coverage
- review states and variants
- review naming logic
- improve clarity and scalability
- prepare the system for documentation, handoff, or growth

## Goal
The goal of this skill is to review a design system in a practical and analytical way to determine whether it is coherent, clear, scalable, and appropriate for the product’s needs.

This skill should help:
- identify what already exists in the system
- uncover issues in foundations, tokens, or components
- detect inconsistency
- identify gaps in components or states
- expose naming or structural issues
- clarify what needs improvement or reorganization
- support the creation of a stronger and more usable system

## Input type
The user may provide:
- a design system description
- a component list
- a foundations list
- a token structure
- naming examples
- screenshots described in text
- a documentation summary
- notes explaining what has already been built
- a description of a UI kit or library

The input may be complete, partial, or not fully documented.

## Instructions
When using this skill, review the current system from the perspective of consistency, coverage, clarity, scalability, and usability.

### 1) Understand the nature of the system first
Determine:
- what kind of product this system supports
- whether the system seems generic or tied to a specific product
- whether it is intended for mobile, dashboard, SaaS, or a multi-role platform
- whether the available information is enough for a useful review

### 2) Review the foundations
Check the quality of foundations such as:
- colors
- typography
- spacing
- radius
- borders
- shadows
- grid or layout logic
- iconography
- imagery direction if present

Check whether they are:
- clear
- consistent
- appropriate for the product
- not overbuilt
- actually usable in practice

### 3) Review the tokens
Check:
- whether there is a clear token structure
- whether primitive and semantic tokens are separated properly
- whether naming is logical
- whether the system is easy to use in Figma or handoff
- whether there is confusion between value-based and usage-based naming
- whether there is duplication or lack of clarity

### 4) Review component coverage
Check whether the current components cover the actual needs of the product.
Review:
- whether the essential components exist
- whether important components are missing
- whether some components were built too early
- whether there are too many components without a clear structure
- whether there are gaps between what the product needs and what the system includes

### 5) Review states and variants
For each important component, check:
- whether the core states exist
- whether interaction states are clear
- whether status states are included
- whether size variants are logical
- whether the variants serve real needs or feel excessive
- whether missing states may cause future issues

### 6) Review naming logic
Check whether the naming is:
- clear
- consistent
- scalable
- easy for the team to understand
- suitable for handoff
- free from ambiguity or conflict

Look for issues such as:
- names that are too visual rather than functional
- mixed naming patterns
- inconsistency between component names and token names
- names that are too long or impractical

### 7) Review organization and structure
Check whether the system is organized in a way that supports:
- searchability
- understanding
- reuse
- scalability
- onboarding of new team members

For example, review:
- whether component groups are logical
- whether foundations are clearly separated
- whether variants are organized properly
- whether the documentation is understandable

### 8) Detect gaps and risks
Mention what is missing or what may cause issues later, such as:
- missing semantic tokens
- missing states
- unclear component boundaries
- repeated components
- over-complex variants
- lack of documentation
- weak naming logic
- a system that is too generic or too product-specific
- poor scalability for future needs

### 9) Give practical recommendations
Suggest clear improvements such as:
- reorganizing the token structure
- separating primitive from semantic tokens
- unifying the naming pattern
- reducing unnecessary variants
- adding missing states
- building core components before complex ones
- improving grouping
- documenting usage rules

### 10) Separate what is already strong from what needs improvement
Do not make the review purely negative.
Mention:
- what is working well
- what already feels strong
- what only needs refinement
- what may need rethinking

## Output format
Always structure the response like this:

1. Quick Summary of the Current System  
A short explanation of the design system and what it appears to cover.

2. What Works Well  
Mention the strong parts of the system.

3. Notes on Foundations  
Review foundations such as colors, typography, spacing, and related basics.

4. Notes on Tokens and Naming  
Review the token structure and naming logic.

5. Notes on Components  
Review component coverage, quality, and organization.

6. Missing or Weak States and Variants  
Mention what is missing, unclear, or weak.

7. Structural Risks or System Issues  
Mention issues that may affect scalability, consistency, or handoff.

8. Suggested Improvements  
Provide practical and direct recommendations.

9. Suggested Priorities  
Mention what should be fixed first.

10. Unclear Points  
Mention what still needs clarification if the input is incomplete.

## Tone
The tone should be:
- clear
- analytical
- practical
- design-system-oriented
- product-aware
- direct
- free from filler

## Rules
- Do not give generic feedback without a clear reason.
- Do not invent elements or structures that are not present in the input.
- Clearly separate confirmed findings from inferred concerns.
- If something is inferred, explicitly label it as inferred.
- Do not turn the response into a full rebuild of the system unless the user asks for that.
- Focus on consistency, scalability, usability, and system clarity.
- Do not overcomplicate the system if the product is still at MVP stage.
- Make the result genuinely useful for product, design, documentation, or handoff work.

## What good output looks like
A strong response should help the user:
- understand the quality of the current design system
- uncover real gaps and weaknesses
- prioritize improvements
- build a more consistent and scalable system
- improve handoff and team collaboration around the system