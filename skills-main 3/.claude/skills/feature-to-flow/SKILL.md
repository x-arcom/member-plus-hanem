---
name: feature-to-flow
description: Convert a feature description, product requirement, or raw idea into a clear, structured user flow that includes steps, system behavior, decisions, states, and key transitions before design.
---

# Feature to Flow Skill

## When to use this skill
Use this skill when the user provides:
- a feature description
- a product requirement
- a business rule
- an idea for a new feature
- a workflow summary
- a raw product note
- a draft PRD
- acceptance criteria
- a rough explanation of how something should work

Use this skill when the goal is to:
- turn a feature into a structured flow
- understand the sequence of steps
- identify user actions and system responses
- define decisions and branching logic
- prepare for UX design
- prepare for wireframes
- clarify the path before reviewing or testing it

## Goal
The goal of this skill is to transform a raw feature idea or requirement into a practical product flow.

This skill should help:
- identify the starting point of the flow
- define the key user steps
- identify system reactions
- surface decision points
- identify possible branches
- expose missing states
- organize the feature into a usable experience
- make the logic easier to review before design

## Input type
The user may provide:
- a feature description
- a requirement document
- a short explanation
- raw notes
- meeting notes
- workflow text
- user story
- acceptance criteria
- business rules

The input may be incomplete, unstructured, or partially unclear.

## Instructions
When using this skill, analyze the feature carefully and convert it into a clear flow.

### 1) Understand the purpose of the feature
Determine:
- what the feature is trying to do
- what user problem it solves
- whether it is a standalone flow or part of a larger product flow
- who the main actor is

### 2) Identify the trigger or starting point
Define how the flow starts.
Examples:
- user clicks a button
- user opens a page
- user receives a notification
- admin creates a record
- system detects an event
- merchant selects an action

Clearly state the entry point.

### 3) Identify the main actor
Determine who is performing the flow:
- customer
- admin
- merchant
- parent
- teacher
- provider
- support agent
- system

If multiple actors are involved, identify the main actor first and mention where other roles are involved.

### 4) Break the flow into step-by-step stages
Convert the feature into sequential steps.
Each step should describe:
- what the user does
- what the system shows
- what the system does
- what happens next

The steps should be practical and ordered.

### 5) Identify decisions and branching logic
If the flow contains choices, conditions, or state-based behavior, clearly mention:
- what the condition is
- what happens if the condition is met
- what happens if it is not met

Examples:
- if the campaign is in Draft, show the action
- if the phone number is invalid, block submission
- if quota is exhausted, show warning and CTA
- if payment fails, show retry path

### 6) Identify system states
Surface the important states involved in the flow, such as:
- default state
- loading state
- empty state
- disabled state
- success state
- error state
- exhausted state
- validation state
- pending state
- completed state

Do not invent unnecessary states, but do not miss obvious ones.

### 7) Highlight missing or unclear flow points
If the requirement is unclear, mention:
- missing transitions
- unclear ownership
- unclear next step
- undefined branch logic
- missing system response
- missing state
- missing exception path

### 8) Keep the flow practical
Do not turn the response into UI design suggestions unless necessary.
Focus on:
- logic
- sequencing
- actors
- states
- transitions
- decision points

### 9) Support design readiness
Structure the result in a way that makes it easy to move into:
- wireframes
- UX flows
- screen planning
- review
- handoff
- test case writing

## Output format
Always structure the response like this:

1. Feature Summary  
A short explanation of what the feature does.

2. Main Actor  
Who performs the flow.

3. Entry Point  
How the flow starts.

4. Step-by-Step Flow  
A clear ordered list of the main flow steps.

5. Decision Points and Branches  
Important conditions and alternate paths.

6. Key States  
The important states that appear in the flow.

7. Missing or Unclear Areas  
Anything that still needs clarification.

8. Suggested Next Step  
What the user should do next, such as review requirements, review the flow, design screens, or write test cases.

## Tone
The tone should be:
- clear
- structured
- practical
- product-oriented
- UX-aware
- direct

## Rules
- Do not invent product details that are not supported by the input.
- Clearly separate confirmed flow logic from inferred logic.
- If something is inferred, label it as inferred.
- Focus on flow logic, not visual design.
- Do not skip states or branching points if they are clearly relevant.
- Keep the flow actionable and useful for the next product step.
- If the feature is too vague, say what needs clarification before the flow can be finalized.
- Avoid generic wording.
- Keep the response usable for actual product work.

## What good output looks like
A strong response should help the user:
- understand how the feature actually works
- see the full sequence of steps
- spot missing flow logic
- identify branches and states
- move more easily into design, review, and testing
