---
name: write-test-cases
description: Generate clear, structured, and practical test cases from a feature description, requirement, flow, scenarios, or acceptance criteria, including positive, negative, validation, and relevant edge cases.
---

# Write Test Cases Skill

## When to use this skill
Use this skill when the user provides:
- a feature description
- a requirement
- a user flow
- scenarios
- acceptance criteria
- business logic
- product notes
- a PRD draft
- a description of expected behavior

Use this skill when the goal is to:
- write structured test cases
- prepare QA coverage
- validate a feature before release
- convert product logic into testable cases
- cover happy paths, negative cases, validations, and key edge cases
- support product, QA, and development alignment

## Goal
The goal of this skill is to turn product requirements or flows into practical and well-structured test cases that are easy to review and use.

This skill should help:
- cover the main happy path
- cover important negative cases
- cover validation behavior
- cover permissions or state-based behavior when relevant
- identify important missing test coverage
- keep each test case focused and usable
- make feature behavior easier to verify

## Input type
The user may provide:
- a feature description
- a requirement
- a flow
- scenarios
- acceptance criteria
- raw notes
- a summary of expected behavior
- screenshots described in text
- business rules

The input may be complete or partial.

## Instructions
When using this skill, analyze the feature carefully, then generate clear and practical test cases.

### 1) Understand the feature first
Determine:
- what the feature does
- who the main actor is
- what the expected outcome is
- whether the feature has validations, permissions, statuses, or branching logic
- whether the input is strong enough to generate reliable test cases

### 2) Cover the main types of test cases
Generate test cases that cover, when relevant:
- happy path
- validation cases
- negative cases
- blocked or restricted actions
- state-based behavior
- permission-based behavior
- success and error handling
- important edge cases

Do not force unnecessary coverage, but do not miss clearly relevant coverage.

### 3) Keep each test case focused
Each test case should test one clear behavior or scenario.
Do not combine unrelated checks into one test case.

### 4) Use practical preconditions
Preconditions should clearly describe what must already be true before the steps begin.

### 5) Write clear test steps
Test steps should:
- be sequential
- be easy to follow
- describe user or system actions clearly
- avoid unnecessary detail
- stay tied to the scenario being tested

### 6) Write specific expected results
Expected results should clearly describe:
- what should happen
- what should not happen
- what the user should see
- what state or behavior should remain unchanged when relevant

### 7) Cover validations and restrictions
If the feature includes:
- required fields
- invalid inputs
- disabled states
- state restrictions
- quota restrictions
- permissions
- missing dependencies

make sure the test cases reflect those clearly.

### 8) Mention unclear assumptions when needed
If some logic is not fully defined, mention that certain test cases are based on inferred assumptions, or highlight what still needs clarification.

### 9) Keep the result useful for real QA and product work
The output should be practical and ready to use, not theoretical.

## Output format
For each test case, always use this structure:

**Test Case ID:**  
**Test Case Title:**  
**Preconditions:**  
**Test Steps:**  
1.  
2.  
3.  

**Expected Result:**  

## Tone
The tone should be:
- clear
- structured
- practical
- QA-aware
- product-aware
- direct

## Rules
- Do not combine multiple unrelated scenarios in one test case.
- Do not generate vague test cases.
- Do not invent unsupported behavior.
- If something is inferred, explicitly label it as inferred.
- Keep titles specific and meaningful.
- Keep the result usable for actual QA and product review.
- If the input is too vague, say what needs clarification before full coverage is possible.
- Do not turn the response into a requirement review unless clarification is needed first.

## What good output looks like
A strong response should help the user:
- verify the feature behavior clearly
- cover important scenarios
- reduce missed cases
- align product, QA, and engineering around expected behavior
- move more confidently toward release