---
name: component-spec-writer
description: Write a clear and practical specification for any design system or product UI component, including purpose, usage, states, variants, behavior, rules, and notes for documentation or handoff.
---

# Component Spec Writer Skill

## When to use this skill
Use this skill when the user provides:
- a component name
- a component description
- behavior for a specific component
- states or variants
- usage notes
- part of a design system
- a UI element that needs documentation
- a component that needs clear handoff

Use this skill when the goal is to:
- write a clear spec for a component
- document component behavior
- define states and variants
- support development handoff
- prepare design system documentation
- align the team around how the component should be used

## Goal
The goal of this skill is to turn a component idea or description into a clear, practical, and structured specification that can be used in design, documentation, and development.

This skill should help:
- explain what the component is
- define when it should and should not be used
- define variants
- define important states
- clarify behavior
- clarify usage rules
- support consistency inside the design system
- make handoff clearer and easier

## Input type
The user may provide:
- a component name
- a general description
- a behavior summary
- a list of variants
- a list of states
- usage notes
- requirements related to the component
- product or design system context
- notes from Figma or a documentation draft

The input may be complete or partial.

## Instructions
When using this skill, analyze the component and its context, then write a clear and practical specification.

### 1) Understand the component first
Determine:
- what the component is called
- what role it plays in the product
- what problem or function it serves
- whether it is a foundational or composite component
- whether it is used broadly or only in a limited context

### 2) Explain its purpose
Clearly describe:
- why the component exists
- what it helps the user do
- what kind of information or action it represents

### 3) Define when to use it and when not to use it
Clarify:
- the right situations for using the component
- the situations where it should not be used
- whether another component would be more appropriate in some cases

### 4) Define the variants
If the component has multiple types, mention:
- the main variants
- the difference between them
- when each variant should be used
- when a certain variant would not be appropriate

Examples:
- Button: primary / secondary / ghost / destructive
- Alert: info / success / warning / error
- Card: default / stat / actionable

### 5) Define the states
List the important component states such as:
- default
- hover
- active / pressed
- focus
- disabled
- loading
- success
- error
- selected
- expanded / collapsed
- empty
- readonly
- pending

Do not add unnecessary states, but do not ignore clearly important ones.

### 6) Explain behavior
Describe:
- how the component behaves during interaction
- what happens on click, input, or selection
- how it responds across different states
- whether there is validation, feedback, or transition behavior
- whether behavior depends on status, permissions, or data conditions

### 7) Define structure or content if relevant
If the component is composite, mention what it contains, such as:
- title
- subtitle
- icon
- action
- helper text
- badge
- metadata
- footer
- inline message

### 8) Write usage rules
Mention practical rules such as:
- minimum or maximum content length
- label clarity
- when helper text should appear
- when error state should appear
- when the action should be blocked
- when loading should be shown
- how action hierarchy should be handled inside the component

### 9) Mention accessibility considerations if relevant
Such as:
- labels
- focus visibility
- keyboard interaction
- contrast awareness
- clear error communication
- action clarity

### 10) Add documentation or handoff notes
If relevant, mention:
- what developers should know
- what designers should pay attention to
- what may still need a product decision
- what is still unclear

## Output format
Always structure the response like this:

1. Component Name  
A clear name for the component.

2. Purpose  
What the component does and why it exists.

3. When to Use  
The right situations for using it.

4. When Not to Use  
The cases where it should not be used.

5. Variants  
List the main variants and when each one is appropriate.

6. States  
List the important states for the component.

7. Behavior  
Explain how the component behaves across interactions and states.

8. Structure or Internal Content  
Mention what the component contains if relevant.

9. Usage Rules  
List the practical rules and important notes.

10. Accessibility Considerations  
Mention what should be considered from an accessibility perspective.

11. Documentation or Handoff Notes  
Mention important notes for the team.

## Tone
The tone should be:
- clear
- structured
- practical
- design-system-oriented
- product-aware
- direct
- free from filler

## Rules
- Do not write specs that are too generic to be useful.
- Do not invent behavior that is not supported by the input.
- If something is inferred, explicitly label it as inferred.
- Keep the specification practical and usable.
- Do not focus only on visual appearance.
- The spec should support understanding, documentation, and handoff.
- Do not overcomplicate simple components, but do not oversimplify them so much that the meaning is lost.
- If some parts are unclear, mention what still needs clarification.

## What good output looks like
A strong response should help the user:
- document the component clearly
- align the team around the component
- improve development handoff
- build a clearer and more consistent design system
- reduce ambiguity in behavior or usage