---
name: heuristic-review
description: Review a screen, flow, or digital experience using UX and usability heuristics to identify issues, connect them to the right principle, and suggest practical improvements.
---

# Heuristic Review Skill

## When to use this skill
Use this skill when the user provides:
- a single screen
- multiple screens
- a user flow
- a journey
- a form
- an onboarding experience
- a dashboard
- a checkout flow
- a mobile experience
- a description of an interface or experience

Use this skill when the goal is to:
- run a professional usability review
- identify UX issues in a structured way
- connect findings to UX heuristics
- improve usability
- strengthen the experience before handoff, development, or testing

## Goal
The goal of this skill is to review the interface, flow, or experience through the lens of known usability principles, not just general opinion.

This skill should help:
- identify clarity issues
- identify consistency issues
- identify control and flexibility issues
- identify error prevention and feedback issues
- uncover unnecessary cognitive load
- detect points that may confuse users
- suggest practical improvements tied to a clear reason

## Input type
The user may provide:
- a screen description
- a flow
- a sequence of steps
- a wireframe summary
- an interaction summary
- a text description of a full or partial experience
- screenshots described in text
- a feature described from a usability perspective

The input may be partial, brief, or may describe a single interface or a full journey.

## Principles to use
Review the experience using these usability principles:

1. Visibility of system status  
Does the system clearly show the user what is happening?

2. Match between the system and the real world  
Are the language, concepts, and labels aligned with the user’s mental model?

3. User control and freedom  
Can the user go back, cancel, undo, or recover when needed?

4. Consistency and standards  
Are elements and behaviors consistent across the experience?

5. Error prevention  
Does the design help prevent mistakes before they happen?

6. Recognition rather than recall  
Does the interface reduce the need for users to remember information?

7. Flexibility and efficiency of use  
Is the flow easy for new users and efficient for returning users?

8. Aesthetic and minimalist design  
Is the experience free from unnecessary clutter, overload, or distraction?

9. Help users recognize, diagnose, and recover from errors  
If an error happens, is it clear, understandable, and actionable?

10. Help and guidance  
Does the interface provide enough support, guidance, or explanation when needed?

## Instructions
When using this skill, review the experience carefully using the principles above.

### 1) Understand the context first
Determine:
- what the screen or flow is trying to help the user accomplish
- who the main user is
- whether this is a standalone step or part of a larger journey
- whether the information is sufficient for a meaningful review

### 2) Review each heuristic practically
Do not just mention heuristic names.
Actively check whether issues related to each principle are present when relevant.

### 3) Mention only important issues
Do not fill the response with weak or cosmetic comments.
Focus on:
- issues that affect understanding
- issues that may cause mistakes
- issues that may create hesitation or drop-off
- issues that affect efficiency
- issues that weaken trust or clarity

### 4) Connect each issue to the right principle
Every issue should be clearly tied to the most relevant heuristic.
Example:
- Issue: There is no feedback after clicking the button
- Heuristic: Visibility of system status

### 5) Give practical recommendations
After each finding, or in the improvement section, give a clear recommendation that could realistically be applied.
Avoid vague suggestions such as:
- improve the interface
- make it clearer
- simplify the design

Instead say things like:
- add a clear loading state after submission
- show helper text before input
- make the secondary action less visually prominent than the primary action
- add a confirmation state after success

### 6) Separate confirmed issues from inferred concerns
If some findings are based on an incomplete description, clearly mark them as:
**Inferred concerns**
rather than confirmed issues.

### 7) Do not turn the review into a purely visual critique
This skill should not focus on aesthetic preferences unless they directly affect:
- clarity
- sequence
- understanding
- usability

### 8) Make the result useful for the next step
The review should help the user:
- improve the experience
- understand priorities
- prepare a stronger handoff
- strengthen the flow or screen before launch

## Output format
Always structure the response like this:

1. Quick Summary  
A short explanation of what the screen or flow appears to be trying to achieve.

2. What Works Well  
Mention the strong parts of the experience.

3. Issues by Heuristic  
Group issues under the relevant heuristic, such as:
- Visibility of system status
- User control and freedom
- Error prevention
- Minimalist design
- etc.

4. Highest-Priority Issues  
List the issues that most affect usability and should be addressed first.

5. Suggested Improvements  
Give practical and direct recommendations.

6. Unclear Points  
Mention anything that still needs clarification if the input is incomplete.

## Tone
The tone should be:
- clear
- professional
- analytical
- direct
- practical
- UX-oriented
- free from filler

## Rules
- Do not give generic feedback without a clear reason.
- Do not repeat the same issue in different words.
- Do not invent details that are not present in the input.
- Clearly separate confirmed issues from inferred concerns.
- If something is inferred, explicitly label it as inferred.
- Do not make the review purely aesthetic.
- Tie each issue to the most relevant heuristic.
- Focus on issues that affect understanding, behavior, trust, or task completion.
- Make the response useful for real product work.

## What good output looks like
A strong response should help the user:
- understand usability issues professionally
- understand why each issue exists
- connect the issue to a clear UX principle
- prioritize improvements more effectively
- improve the experience in a practical way before handoff or development