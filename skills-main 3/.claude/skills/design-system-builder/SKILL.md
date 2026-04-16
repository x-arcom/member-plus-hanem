---
name: design-system-builder
description: Build a practical and structured design system based on the product type and its needs by defining foundations, tokens, component groups, states, naming logic, and usage rules in a way that supports a scalable and consistent product experience.
---

# Design System Builder Skill

## When to use this skill
Use this skill when the user provides:
- a new product idea
- a new project
- a product or platform brief
- a description of interfaces or modules
- a need to build a design system from scratch
- a need to organize UI foundations
- a need to identify required components
- a need to prepare a design system foundation before detailed UI design starts

Use this skill when the goal is to:
- build a design system that fits the product
- define clear foundations
- organize tokens
- propose a component structure
- define states and variants
- create naming logic
- support consistency and future scale

## Goal
The goal of this skill is to help the user build a practical, coherent, and usable design system, not just a generic list of UI elements.

This skill should help:
- understand the product type and its needs
- define the right visual and functional foundation
- propose foundations such as colors, typography, and spacing
- identify the core components the product needs
- suggest logical states and variants
- organize design tokens
- create a clear system structure
- support consistency and scalability across screens

## Input type
The user may provide:
- a project description
- a product type
- a brand name
- main user types
- modules or features
- a style direction
- brand values
- references
- UI needs
- raw notes about the needed system

The input may be complete, partial, or still at an early stage.

## Instructions
When using this skill, analyze the product and its needs, then build a suitable design system in a practical and structured way.

### 1) Understand the product type first
Determine:
- what type of product this is
- the context in which it will be used
- who the main users are
- whether the product is mobile-first, dashboard-heavy, or a multi-role platform
- whether it needs simple, operational, educational, SaaS, enterprise, consumer, or other interface patterns

### 2) Define the core foundations
Propose the right foundations for the product, such as:
- Color system
- Typography system
- Spacing scale
- Radius system
- Shadow usage
- Border logic
- Grid or layout foundations
- Icon style direction
- Illustration or imagery direction if relevant

The foundations must be tied to the product type, not generic by default.

### 3) Define the design tokens
Propose a clear token structure, such as:
- primitive tokens
- semantic tokens
- usage-based tokens

Examples:
- colors: primary-500, gray-100
- semantic: text-primary, surface-secondary, border-muted, bg-success
- spacing: 4, 8, 12, 16...
- radius: sm, md, lg...
- typography: heading-lg, body-md, label-sm

### 4) Define the main component groups
Break the system into logical groups of components, such as:
- Buttons
- Inputs
- Selectors
- Cards
- Navigation
- Modals
- Tables
- Tabs
- Alerts
- Empty states
- Loaders
- Badges
- Dropdowns
- Tooltips
- Toasts
- Pagination
- Data display components

The groups should be based on the actual product needs.

### 5) Identify the most important starting components
Based on the product, propose the key components that should be built first.
Examples:
- If the product is dashboard-heavy: tables, filters, stat cards, side navigation, pagination
- If the product is a mobile app: bottom navigation, cards, list items, modal sheets, empty states
- If the product is educational: lesson cards, progress indicators, quizzes, badges, timeline blocks

### 6) Define states and variants
For each major component, suggest:
- core states
- interaction states
- status states
- size variants
- intent variants when relevant

Examples:
- Button: default, hover, pressed, disabled, loading
- Input: default, focus, error, success, disabled
- Alert: info, success, warning, error

### 7) Propose naming logic
Suggest a naming system that supports:
- consistency
- clarity
- scalability
- better handoff

Examples:
- button/primary/default
- input/text/error
- card/stat/default
- color/text/primary
- spacing/16
- radius/md

### 8) Consider scalability
The system should work for:
- the MVP now
- future growth later
without becoming unnecessarily large too early

Mention what should likely be included in:
- v1
- phase 2 or later
when relevant

### 9) Keep the system tied to the product
Do not generate a generic design system.
Recommendations must be connected to:
- the product type
- its interface patterns
- its complexity level
- how it is used
- differences between user types if relevant

### 10) Call out decisions that still depend on the designer or team
If some parts depend on a visual direction, brand choice, or product decision, state that clearly.
Examples:
- level of formality
- warm vs technical tone
- illustrative vs minimal system
- dense vs spacious layout approach

## Output format
Always structure the response like this:

1. Quick Product Summary  
A short explanation of the product type and what it needs from a design system.

2. Recommended Foundations  
List the key foundations that fit the product.

3. Design Token Structure  
Propose a clear structure for the tokens.

4. Component Groups  
List the main component groups.

5. Priority Components to Build First  
List the first components that should be built in v1.

6. Important States and Variants  
List the key states and variants that should be considered.

7. Suggested Naming Logic  
Describe the naming approach.

8. What Should Be Included in v1  
List what should be built now.

9. What Can Be Deferred  
List what can wait for a later phase.

10. Open Decisions  
List what still needs a decision from the team or designer.

## Tone
The tone should be:
- clear
- structured
- practical
- product-aware
- design-system-oriented
- direct
- free from filler

## Rules
- Do not build a generic system that is disconnected from the product.
- Do not suggest elements that do not serve the product type.
- Do not overbuild a huge system if the product is still at MVP stage.
- Keep recommendations realistic and usable.
- Separate what is essential now from what can be delayed.
- If something is inferred, explicitly label it as inferred.
- Tie each recommendation to the product and its interfaces.
- Do not turn the response into a full brand guideline unless the user asks for that.
- Make the output useful for actual Figma work or design system documentation.

## What good output looks like
A strong response should help the user:
- start a design system in a logical way
- avoid randomness in building the UI kit
- know what to build first
- organize foundations and tokens more clearly
- build a scalable system without unnecessary complexity