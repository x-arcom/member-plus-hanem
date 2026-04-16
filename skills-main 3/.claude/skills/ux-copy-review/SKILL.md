---
name: ux-copy-review
description: Review interface copy across screens, flows, and interactive elements to identify clarity issues, ambiguity, weak action language, inconsistent tone, or missing guidance, then suggest practical improvements.
---

# UX Copy Review Skill

## When to use this skill
Use this skill when the user provides:
- a screen
- a flow
- button text
- empty states
- helper text
- error messages
- onboarding copy
- success messages
- modal copy
- dashboard text
- labels and validation messages
- product microcopy or any wording inside the interface

Use this skill when the goal is to:
- review UX writing quality
- improve clarity and usability
- make actions easier to understand
- reduce ambiguity
- improve consistency of tone and terminology
- strengthen guidance inside the experience
- improve the quality of product microcopy before handoff or launch

## Goal
The goal of this skill is to review product copy and microcopy from a UX perspective, not as marketing writing and not as grammar-only editing.

This skill should help:
- identify unclear wording
- identify weak or ambiguous CTAs
- identify missing guidance
- identify inconsistent terminology
- identify copy that is too long or too complex
- improve action clarity
- improve user confidence and understanding
- make the experience easier to follow through language

## Input type
The user may provide:
- full screen copy
- step-by-step flow copy
- button labels
- labels and helper text
- validation messages
- success and error messages
- onboarding content
- modal content
- raw product text
- a Figma summary
- screenshots described in text

The input may be complete, partial, polished, or still in draft form.

## Instructions
When using this skill, review the text from a UX writing perspective inside the product.

### 1) Understand the context first
Determine:
- what the user is trying to do
- where this copy appears
- whether the text is for an action, explanation, system feedback, or guidance
- whether the context is onboarding, a form, an error, a modal, a dashboard, or another product surface

### 2) Review clarity
Check whether:
- the wording is easy to understand
- the user can quickly understand what the action or message means
- the wording avoids ambiguity
- the text communicates what matters without unnecessary complexity

### 3) Review CTA strength
Check whether:
- buttons and action labels are clear
- the CTA reflects the actual outcome
- the language is specific enough
- the action feels understandable and decisive

Examples of weak copy:
- Continue
- Submit
- Confirm

when the user may need more context to understand the result.

### 4) Review consistency
Check whether:
- the same concept is referred to using the same term across the experience
- labels, messages, and statuses use consistent wording
- the tone remains aligned across similar screens and actions

### 5) Review guidance and helpfulness
Check whether:
- helper text exists where needed
- users are told what to do when the context may be unclear
- error messages tell users how to recover or fix the issue
- empty states guide users toward the next step
- messages reduce uncertainty

### 6) Review tone and appropriateness
Check whether:
- the tone fits the product and context
- the wording is too formal, too vague, too robotic, or too casual
- the language feels aligned with the product experience
- critical moments use calm and clear language

### 7) Review length and density
Check whether:
- the copy is too long for the context
- important messages are buried inside dense text
- labels are too short to be meaningful
- explanations could become clearer with fewer words

### 8) Identify missing copy opportunities
Mention if the experience seems to need:
- helper text
- confirmation copy
- better empty state guidance
- clearer validation messages
- stronger action labels
- better success or error feedback

### 9) Suggest practical improvements
Do not only criticize the copy.
Suggest better wording when useful.
Recommendations should be practical and tied to the context.

### 10) Separate confirmed issues from inferred concerns
If the context is incomplete, clearly mark some findings as:
**Inferred concerns**
rather than fully confirmed issues.

## Output format
Always structure the response like this:

1. Quick Summary  
A short explanation of what the copy appears to support in the experience.

2. What Works Well  
Mention the strong parts of the copy.

3. Issues Found  
List the main clarity, consistency, tone, or usability issues.

4. Weak or Unclear Copy Areas  
Mention specific labels, messages, or text areas that need improvement.

5. Suggested Copy Improvements  
Provide improved wording where helpful.

6. Missing Copy Opportunities  
Mention what seems to be missing in the experience.

7. Unclear Points  
Mention anything that still needs clarification.

## Tone
The tone should be:
- clear
- practical
- UX-writing-aware
- direct
- professional
- constructive

## Rules
- Do not review the copy as if it were marketing content.
- Do not focus only on grammar.
- Focus on clarity, usability, consistency, and actionability.
- Do not invent product behavior that is not supported by the input.
- Clearly separate confirmed issues from inferred concerns.
- If something is inferred, explicitly label it as inferred.
- Make the output useful for real product writing and design work.
- Avoid generic comments.
- Recommendations should fit the specific context.

## What good output looks like
A strong response should help the user:
- improve product clarity through language
- make actions and messages easier to understand
- create stronger CTA labels and clearer feedback
- reduce ambiguity and confusion
- build more usable and more consistent product copy