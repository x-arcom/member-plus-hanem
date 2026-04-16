---
name: accessibility-review
description: Review a screen, flow, or digital experience from an accessibility perspective to identify usability barriers, missing accessibility considerations, and practical improvements for more inclusive use.
---

# Accessibility Review Skill

## When to use this skill
Use this skill when the user provides:
- a screen
- multiple screens
- a flow
- a form
- a dashboard
- a modal
- an onboarding experience
- a mobile experience
- an empty state
- an error state
- a text description of an interface or interaction

Use this skill when the goal is to:
- review accessibility considerations
- identify usability barriers
- improve clarity and readability
- improve inclusive interaction
- strengthen the experience before development or handoff
- catch accessibility issues early

## Goal
The goal of this skill is to review the interface or flow from an accessibility perspective and identify issues that may prevent users from understanding, navigating, or completing tasks effectively.

This skill should help:
- identify readability issues
- identify unclear labels or instructions
- identify missing feedback or focus states
- identify possible interaction barriers
- uncover accessibility weaknesses in forms, actions, states, and navigation
- suggest practical improvements that make the experience more inclusive

## Input type
The user may provide:
- a screen description
- a flow
- a sequence of steps
- a component description
- a wireframe summary
- screenshots described in text
- a feature explanation
- a text summary of a product experience

The input may be complete or partial.

## Review areas
Review the experience using the following accessibility-focused areas when relevant:

1. Clarity of labels and instructions  
Are fields, buttons, actions, and controls clearly labeled?

2. Readability and content clarity  
Is the text easy to understand, concise, and well-structured?

3. Contrast and visual distinction  
Are important elements likely to be visually distinguishable from their background and from each other?

4. Focus and keyboard interaction  
If relevant, does the experience appear to support focus visibility, clear tab order, and keyboard accessibility?

5. Form accessibility  
Are fields, errors, helper texts, required states, and validations likely to be understandable?

6. Feedback and state communication  
Are loading, success, error, disabled, and empty states clearly communicated?

7. Error prevention and recovery  
Can users understand what went wrong and how to fix it?

8. Action clarity and interaction safety  
Are primary and secondary actions easy to distinguish? Are destructive or high-impact actions clear enough?

9. Navigation and orientation  
Can the user understand where they are, what step they are in, and what comes next?

10. Inclusive usability considerations  
Does the experience appear to reduce confusion, overload, and unnecessary dependency on memory, precision, or visual interpretation?

## Instructions
When using this skill, review the interface or flow carefully from an accessibility and inclusive usability perspective.

### 1) Understand the context first
Determine:
- what the user is trying to do
- what kind of interface or flow this is
- who the main user is
- whether the experience includes forms, actions, states, or navigation complexity

### 2) Focus on meaningful accessibility issues
Do not turn the review into a technical compliance checklist only.
Focus on real barriers that may affect:
- understanding
- reading
- interaction
- navigation
- error recovery
- task completion

### 3) Review labels, guidance, and text clarity
Check whether:
- labels are explicit enough
- instructions are clear
- helper text exists where needed
- action names are understandable
- the wording reduces ambiguity

### 4) Review states and feedback
Check whether:
- loading is visible
- errors are understandable
- success is confirmed clearly
- disabled actions are explained when needed
- empty states are helpful

### 5) Review interaction safety and clarity
Check whether:
- users can identify the main action
- secondary actions are not confusing
- risky actions are properly communicated
- confirmation or recovery exists when needed

### 6) Review accessibility of forms and inputs
Check whether:
- fields appear to have labels
- required information is understandable
- validation guidance is clear
- error messages are actionable
- the input flow is likely to be manageable

### 7) Review likely accessibility risks
Mention issues such as:
- unclear labels
- missing helper text
- ambiguous buttons
- state changes without clear feedback
- unclear error messaging
- likely weak contrast
- over-reliance on color alone
- missing orientation cues
- actions that may be hard to distinguish

### 8) Separate confirmed issues from inferred concerns
If some concerns are based on incomplete input, clearly label them as:
**Inferred concerns**
rather than confirmed issues.

### 9) Make the result practical
The review should help the user improve the product, not just point out problems.
Recommendations should be specific and usable.

## Output format
Always structure the response like this:

1. Quick Summary  
A short explanation of what the screen or flow appears to do.

2. What Supports Accessibility Well  
Mention the parts that seem supportive of accessibility or clarity.

3. Accessibility Issues Found  
List the main barriers or weaknesses found.

4. High-Priority Accessibility Risks  
Mention the most important issues that should be fixed first.

5. Suggested Improvements  
Give practical recommendations.

6. Unclear Points  
Mention anything that still needs clarification.

## Tone
The tone should be:
- clear
- practical
- professional
- inclusive
- direct
- UX-aware

## Rules
- Do not invent visual details that are not present in the input.
- Do not reduce the review to a generic checklist.
- Focus on meaningful user barriers.
- Clearly separate confirmed issues from inferred concerns.
- If something is inferred, explicitly label it as inferred.
- Do not give vague recommendations.
- Keep the result useful for real product and design work.
- Do not overstate certainty when the input is incomplete.

## What good output looks like
A strong response should help the user:
- identify accessibility risks early
- improve clarity and inclusiveness
- make the experience easier to understand and use
- prepare stronger design decisions before implementation