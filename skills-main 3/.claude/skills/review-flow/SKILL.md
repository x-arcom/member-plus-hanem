---
name: review-flow
description: Review a user flow or product flow to identify UX issues, logic gaps, missing states, unclear transitions, friction points, and improvement opportunities before design finalization or implementation.
---

# Review Flow Skill

## When to use this skill
Use this skill when the user provides:
- a user flow
- a product flow
- a step-by-step journey
- an onboarding flow
- a checkout flow
- a dashboard interaction flow
- a feature flow draft
- a wireflow summary
- a written sequence of screens or actions

Use this skill when the goal is to:
- review the quality of a flow
- identify UX friction
- spot missing states or branches
- validate the logic of the sequence
- improve clarity before design or development
- strengthen the flow before writing test cases or handoff

## Goal
The goal of this skill is to review a flow critically and practically in order to identify weaknesses, missing elements, and opportunities to improve usability and product logic.

This skill should help:
- evaluate whether the flow is easy to follow
- detect confusing or unnecessary steps
- identify missing states
- detect missing transitions or branches
- identify unclear actions or next steps
- uncover UX friction or cognitive overload
- point out logic gaps before implementation
- improve readiness for design, testing, or handoff

## Input type
The user may provide:
- a step-by-step flow
- a user journey
- a written sequence of actions
- a flow summary
- a screen-by-screen explanation
- a wireflow description
- a feature flow draft
- screenshots described in text

The input may be complete or partial, and may describe either a full journey or one section of a larger flow.

## Instructions
When using this skill, review the flow carefully from both a UX and product logic perspective.

### 1) Understand the purpose of the flow
Determine:
- what the flow is trying to help the user achieve
- who the main actor is
- whether the flow is standalone or part of a bigger journey
- whether the flow appears complete enough to review

### 2) Review the sequence of steps
Check whether:
- the order of steps is logical
- the user always knows what to do next
- there are unnecessary or repetitive steps
- the transition from one step to another is clear
- the flow starts and ends clearly

### 3) Review CTA clarity
Check whether:
- the main action is obvious at each step
- CTA labels are clear enough
- the next step is visible and understandable
- the flow creates hesitation because actions are unclear

### 4) Review states
Check whether the flow includes or at least accounts for important states such as:
- default
- loading
- empty
- disabled
- validation
- success
- error
- pending
- completed
- blocked
- exhausted
- expired

Do not force unnecessary states, but explicitly mention missing states if they are clearly needed.

### 5) Review branches and alternate paths
Check whether the flow covers:
- alternative paths
- blocked actions
- invalid inputs
- retry behavior
- canceled actions
- state-based restrictions
- different outcomes depending on user choices or system conditions

### 6) Review friction and usability issues
Check for:
- cognitive overload
- too many decisions in one step
- unclear feedback
- unnecessary effort
- hidden dependencies
- unclear entry points
- weak guidance
- possible user drop-off points

### 7) Review flow completeness
Check whether the flow seems incomplete due to:
- missing steps
- missing transitions
- undefined ownership
- unclear system response
- missing confirmation behavior
- missing exception handling
- unclear completion logic

### 8) Review from a product logic perspective
Check whether:
- the flow aligns with the intended feature behavior
- permissions or role-based behavior are respected
- key rules or restrictions are reflected
- system behavior is coherent across steps

### 9) Recommend improvements
Provide practical recommendations, not generic comments.
The review should help the user make the flow more complete, usable, and implementation-ready.

## Output format
Always structure the response like this:

1. Flow Summary  
A short explanation of what the flow appears to do.

2. What Works Well  
Mention the strong parts of the flow.

3. Issues Found  
List the UX, logic, or structure issues found in the flow.

4. Missing States or Paths  
Mention any missing states, branches, or alternate paths.

5. Friction Points  
List any usability or clarity concerns.

6. Suggested Improvements  
Give practical recommendations to improve the flow.

7. Open Questions  
Mention anything that still needs clarification before the flow can be finalized.

## Tone
The tone should be:
- clear
- practical
- direct
- product-minded
- UX-aware
- constructive

## Rules
- Do not simply rewrite the flow.
- Do not focus on visual design unless it directly affects flow clarity.
- Do not invent product behavior that is unsupported by the input.
- Clearly separate confirmed issues from inferred concerns.
- If something is inferred, explicitly label it as inferred.
- Focus on flow quality, logic, usability, and completeness.
- Avoid vague feedback.
- Make the result useful for real product work.

## What good output looks like
A strong response should help the user:
- understand whether the flow is actually strong or weak
- identify missing states and branches
- detect UX friction before design or engineering
- improve the flow before handoff or testing
- ask better follow-up questions if the flow is still incomplete