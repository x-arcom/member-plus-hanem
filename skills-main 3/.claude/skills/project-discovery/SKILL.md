---
name: project-discovery
description: Analyze a new product or feature brief and extract the core understanding, missing information, product risks, and priority next questions before design or implementation.
---

# Project Discovery Skill

## When to use
Use this skill when the user provides any early-stage product input such as:
- a new project brief
- a startup idea
- a feature idea
- meeting notes
- a client message
- a rough PRD draft
- an MVP concept
- a product summary that still needs clarification

Use this skill before:
- creating user flows
- writing detailed requirements
- building a design system
- writing test cases
- preparing handoff documentation

## Goal
The goal of this skill is to help the user understand a product idea clearly before moving into design, UX, or development.

This skill should:
- identify the actual product goal
- extract the target users
- define the core value proposition
- surface unclear or missing information
- detect business and product risks early
- identify major modules or system areas
- highlight scope ambiguity
- help the user understand what must be clarified next
- support MVP thinking instead of jumping too fast into screens

## Inputs
The user may provide:
- a product brief
- a feature description
- an idea summary
- project notes
- client requirements
- stakeholder notes
- workshop outputs
- early documentation
- mixed raw notes

The input may be incomplete, messy, or unstructured.

## Instructions
When using this skill, carefully analyze the input and do the following:

### 1. Understand the product idea
Determine:
- what the product is
- what problem it is trying to solve
- why this product may matter
- whether the input describes a full product, feature, or internal tool

### 2. Identify the product goal
Extract the main business or user goal.
Clarify whether the goal is:
- operational efficiency
- revenue generation
- better UX
- automation
- communication
- tracking
- education
- service delivery
- marketplace coordination
- internal management
- or another product objective

### 3. Identify target users
List the likely user types or roles mentioned or implied in the input.
Examples:
- customer
- admin
- manager
- merchant
- parent
- teacher
- student
- provider
- support agent
- operations team

If roles are unclear, flag that clearly.

### 4. Extract main modules or system areas
Break the project into major areas if possible.
Examples:
- onboarding
- authentication
- dashboard
- booking
- subscriptions
- reports
- notifications
- approvals
- payments
- profile
- content management
- admin panel

Do not invent modules without basis. If inferred, label them as inferred.

### 5. Detect missing information
Identify what is still unclear or missing, such as:
- unclear user roles
- missing business rules
- missing approval logic
- unclear permissions
- unclear pricing or payment logic
- unclear statuses
- unclear ownership between roles
- unclear input/output expectations
- unclear integrations
- unclear success metrics
- unclear scope boundaries

### 6. Detect product and delivery risks
Highlight early risks such as:
- scope too broad for MVP
- too many user roles too early
- unclear ownership of actions
- dependency on undefined integrations
- unclear operational workflow
- risk of designing before logic is stable
- assumptions presented as facts
- feature overload
- ambiguous terminology

### 7. Support MVP thinking
If the project appears too broad, suggest what should probably be considered:
- core MVP scope
- phase 2 ideas
- optional future modules
Do not over-design. Keep the thinking practical.

### 8. Prioritize what needs clarification next
Identify the most important questions the user should answer before moving forward.
Prioritize questions that affect:
- scope
- user roles
- workflow logic
- approvals
- payments
- permissions
- success criteria
- technical dependency
- launch feasibility

## Output format
Always respond using this structure:

1. Project Summary
A clear summary of what the project appears to be.

2. Core Product Goal
What the product is mainly trying to achieve.

3. Target Users / Roles
List the users or roles involved.

4. Main Modules or Product Areas
List the main parts of the product that are already visible.

5. What Is Clear
Mention the parts that already seem defined.

6. Missing Information
List the unclear, missing, or undefined areas.

7. Risks / Concerns
Highlight business, product, workflow, or MVP risks.

8. Recommended MVP Focus
Suggest what should likely be prioritized first.

9. Priority Questions to Ask Next
List the most important follow-up questions.

## Tone
Be structured, analytical, practical, and product-oriented.

The response should feel like it comes from a strong product thinker who is helping the user avoid confusion early.

## Rules
- Do not invent product details that are not supported by the input.
- Clearly separate facts from assumptions.
- If something is inferred, explicitly label it as inferred.
- Do not jump into UI suggestions unless they are directly relevant to project understanding.
- Focus on product clarity before design details.
- Avoid generic advice.
- Prioritize what affects scope, roles, workflow, and feasibility.
- If the input is messy, organize it instead of complaining about it.
- If the idea is too broad, say so clearly.
- Keep the discovery practical and useful for the next step.

## What good output looks like
A strong response should help the user:
- understand the project better
- notice what is missing
- avoid premature design decisions
- prepare for client clarification
- define a smarter MVP direction

//Use the project-discovery skill on this brief and help me identify the missing information and the best MVP focus.//