---
name: feature-to-scenarios
description: Convert a feature description, requirement, or flow into a clear and structured set of scenarios that covers the happy path, alternative paths, negative cases, and edge cases to support stronger product thinking before design or testing.
---

# Feature to Scenarios Skill

## When to use this skill
Use this skill when the user provides:
- a feature description
- a requirement
- a user flow
- business logic
- acceptance criteria
- a PRD draft
- project notes
- an explanation of a new feature
- an early flow that needs to be converted into scenarios

Use this skill when the goal is to:
- extract the main scenarios for a feature
- define the happy path
- identify alternative paths
- identify negative scenarios
- identify edge cases
- understand how the feature behaves in different situations
- prepare a stronger foundation for review, testing, or design

## Goal
The goal of this skill is to convert a feature or flow into a practical set of scenarios that clearly shows how the feature behaves across different situations.

This skill should help:
- identify the main scenario
- extract alternative scenarios
- identify negative cases
- identify exception and edge cases
- uncover missing logic
- clarify what needs to be covered before design or QA
- support structured thinking beyond a single ideal path

## Input type
The user may provide:
- a feature description
- a user flow
- a requirement
- acceptance criteria
- business rules
- raw notes
- an early draft
- a screen or journey description
- a meeting summary

The input may be incomplete, messy, unstructured, or based on assumptions that are not yet confirmed.

## Instructions
When using this skill, analyze the input carefully, then convert it into a clear set of scenarios.

### 1) Understand the feature or journey first
Determine:
- what the feature does
- what its purpose is
- who the main actor is
- what the expected outcome is
- whether the scenario relates to a single action or a full flow

### 2) Start with the Happy Path
Start with the ideal primary scenario:
- when all required conditions are met
- when the flow behaves as expected
- when the user completes the task successfully without issues

This scenario should be clear, specific, and well-structured.

### 3) Extract alternative scenarios
After the main scenario, identify logical alternatives such as:
- a different choice by the user
- a different data condition
- a difference in role or permission
- a difference in item, request, or campaign status
- a different entry point
- another path that leads to the same or similar outcome

### 4) Extract negative scenarios
Identify cases where the flow may fail, be blocked, or behave unexpectedly, such as:
- invalid input
- missing data
- an unmet condition
- an unauthorized attempt
- a state that blocks the action
- execution failure
- validation failure
- quota or limit exhaustion
- missing permission
- connection or loading failure

### 5) Extract edge cases
Identify less common but important cases such as:
- repeated action in a short time
- a state change during execution
- the user leaving midway through the flow
- the user entering from a different entry point
- unexpected data
- boundary cases in values, timing, or roles
- conflicts between multiple conditions
- an item being deleted, expired, or unavailable during execution

### 6) Make sure each scenario has a clear reason
Every scenario should have a valid purpose.
Do not create scenarios just to increase the count.
Each scenario must be:
- realistically possible
- relevant to the experience or logic
- useful for review or testing

### 7) Highlight what is missing
If the input is not detailed enough to produce strong scenarios, explicitly mention:
- what needs clarification
- what cannot be confirmed yet
- which assumptions were used to build the scenarios

### 8) Keep the output useful for the next step
The scenarios should be useful for:
- flow review
- test case writing
- requirement review
- screen and state design
- logic documentation

## Output format
Always structure the response like this:

1. Feature Summary  
A short and clear explanation of what the feature does.

2. Main Actor  
Who the main user or actor is in these scenarios.

3. Main Scenario (Happy Path)  
Describe the ideal core scenario clearly.

4. Alternative Scenarios  
List the logical alternative scenarios.

5. Negative Scenarios  
List the cases where the flow fails, is blocked, or produces a problem.

6. Edge Cases  
List the less common but important cases.

7. Assumptions or Unclear Areas  
Mention what still needs clarification or what was inferred.

8. Suggested Next Step  
Explain what should happen next, such as:
- review the flow
- refine the requirements
- write test cases
- design screens
- document states

## Tone
The tone should be:
- clear
- structured
- practical
- product-oriented
- logical
- direct
- free of filler

## Rules
- Do not invent unrealistic scenarios or scenarios unsupported by the input.
- Clearly separate confirmed scenarios from inferred ones.
- If something is inferred, explicitly label it as inferred.
- Do not stop at the happy path only.
- Do not ignore negative scenarios if they are clearly relevant or likely.
- Do not turn the response into full test cases.
- Do not drift into UI design unless necessary to understand the scenario.
- Keep the scenarios usable for the next product step.
- If the input is too vague, explain what prevents stronger scenario generation.

## What good output looks like
A strong response should help the user:
- understand all important states of the feature
- see beyond the happy path
- discover branches and possible failures
- build a stronger base for review, QA, or design
- notice what is still missing before finalizing the feature