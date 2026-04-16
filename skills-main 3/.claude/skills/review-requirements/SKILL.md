---
name: review-requirements
description: Review a feature description, requirement, or product logic to uncover missing information, ambiguity, missing scenarios, logical risks, and open questions before moving into flow design, UI, or implementation.
---

# Review Requirements Skill

## When to use this skill
Use this skill when the user provides:
- a feature description
- a requirement
- a PRD draft
- acceptance criteria
- business rules
- project notes
- a task description
- workflow logic
- text explaining how a feature should work

Use this skill before:
- building a flow
- starting design
- writing test cases
- preparing handoff
- finalizing feature behavior

## Goal
The goal of this skill is to review requirements in an analytical and structured way in order to uncover what is missing, unclear, incomplete, or risky before moving to the next product step.

This skill should help:
- understand what the requirement is actually describing
- identify what is already clear
- uncover missing information
- uncover missing scenarios
- detect logical conflicts or risks
- notice gaps in permissions, states, or business rules
- identify what must be clarified before design or development
- prevent moving too quickly into UI before the logic is stable

## Input type
The user may provide:
- a feature description
- a requirement document
- acceptance criteria
- a PRD draft
- a user story
- business logic
- raw notes
- a client message
- meeting notes
- a product task description

The input may be incomplete, messy, unstructured, or based on assumptions that are not yet confirmed.

## Instructions
When using this skill, analyze the requirement carefully, then review it from the perspective of product logic, clarity, and completeness.

### 1) Understand what the requirement is describing
Determine:
- what feature or behavior is being requested
- what the purpose of the feature is
- who the main actor or user is
- whether this requirement describes a standalone flow or part of a larger flow
- whether the text describes clear behavior or only a general intention

### 2) Extract what is already clear
Identify the parts that already seem clearly defined, such as:
- explicit conditions
- clear constraints
- a defined role
- a known state
- a specific business rule
- a clear trigger or entry point

Do not confuse confirmed information with inferred information.

### 3) Detect missing or unclear information
Look for unclear or undefined areas such as:
- unclear start or end points
- unclear ownership
- unclear permission logic
- unclear transitions
- unclear status changes
- unclear validations
- unclear error handling
- unclear success behavior
- unclear limits, quotas, or permissions
- unclear dependencies or integrations
- unclear scope boundaries

### 4) Detect missing scenarios
Review whether the requirement only covers the ideal case.
Look for missing scenarios such as:
- negative cases
- invalid inputs
- blocked actions
- expired or unavailable states
- alternative actor behavior
- retry paths
- failed execution
- empty states
- loading states
- permission-related cases
- state-based restrictions
- edge cases

### 5) Review business logic
Check whether the logic is coherent and sufficiently defined.
Look for:
- conflicts between conditions
- missing rules
- unconfirmed assumptions
- undefined dependencies
- a condition mentioned without clear behavior
- an action mentioned without a clear outcome
- a restriction mentioned without explanation
- a state mentioned without transition logic

### 6) Review roles and permissions if relevant
If the requirement includes multiple roles or actors, check:
- who can view the feature
- who can perform the action
- who can edit, approve, cancel, or manage it
- whether permissions differ by state, plan, or type
- whether ownership is clearly defined between roles

### 7) Review states
Check for the presence or absence of important states such as:
- default
- loading
- disabled
- validation
- success
- error
- empty
- pending
- completed
- exhausted
- rejected
- expired

Do not add unnecessary states, but do not miss clearly relevant ones.

### 8) Highlight risks or important observations
Mention anything that may cause problems later, such as:
- the requirement being too broad
- unstable logic
- missing states affecting UX
- unclear ownership
- a likely misunderstanding between product, design, and engineering
- the feature depending on an unresolved decision

### 9) Identify what still needs clarification
Extract the most important questions or points that must be resolved before moving into:
- feature-to-flow
- review-flow
- design
- test cases
- implementation

## Output format
Always structure the response like this:

1. Requirement Summary  
A clear and short explanation of what the requirement is asking for.

2. What Is Clear  
List the parts that already seem defined or known.

3. Missing or Unclear Information  
List what is ambiguous, incomplete, or not yet defined.

4. Missing Scenarios  
List the cases or paths that do not appear to be covered well enough.

5. Logical Risks or Notes  
Mention any issues or concerns related to business logic or requirement structure.

6. Roles and Permissions (if relevant)  
Mention what is clear or missing regarding roles and permissions.

7. Important States  
List the key states that should be considered.

8. Top Clarifications Needed  
List the most important questions or decisions that must be resolved.

9. Suggested Next Step  
For example:
- convert into a flow
- clarify the logic first
- review with the PM or client
- write scenarios
- write test cases later

## Tone
The tone should be:
- clear
- analytical
- practical
- product-oriented
- direct
- concise
- free from unnecessary politeness or filler

## Rules
- Do not invent details that are not present in the input.
- Clearly separate confirmed information from inferred information.
- If something is inferred, explicitly label it as inferred.
- Do not simply paraphrase the requirement.
- Focus on gaps, logic, and risks.
- Do not move into UI design unless it is necessary to understand the issue.
- Do not treat the happy path alone as sufficient.
- If the requirement is broad or ambiguous, say so clearly.
- Make the result genuinely useful for the next product step.

## What good output looks like
A strong response should help the user:
- understand whether the requirement is actually ready or not
- notice gaps before starting flow or design work
- discover missing scenarios
- reduce misunderstandings between product, design, and engineering
- know what must be clarified before moving forward