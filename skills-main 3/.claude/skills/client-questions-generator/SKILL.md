---
name: client-questions-generator
description: Generate smart, structured client questions based on a project brief, feature idea, or early requirement in order to clarify scope, roles, workflow, business rules, and MVP priorities before design or implementation.
---

# Client Questions Generator Skill

## When to use this skill
Use this skill when the user shares:
- an early project brief
- a product idea or MVP concept
- a feature description
- draft requirements
- meeting notes
- a client message
- an early workflow draft
- a rough project summary that needs clarification

Use this skill when the goal is to:
- prepare for a client meeting
- generate discovery questions
- clarify incomplete requirements
- define project scope
- understand business rules
- uncover missing information before design or development

## Goal
The goal of this skill is to help the user generate the most useful questions to ask a client or stakeholder in a practical, structured, and high-value way.

This skill should help:
- uncover ambiguity in the project
- clarify scope
- understand users and roles
- understand workflow logic
- understand payments, pricing, or approvals
- uncover missing business rules
- identify what must be resolved before moving into design or implementation
- avoid weak, generic, or repetitive questions

## Input type
The user may provide:
- a project brief
- a product idea
- early requirements
- a feature description
- raw notes
- a meeting summary
- a flow draft
- a PRD draft
- a client message
- a voice note converted to text

The input may be incomplete, messy, unstructured, or based on assumptions that are not yet confirmed.

## Instructions
When using this skill, first analyze the input, then generate clear and specific questions that help clarify the project in a meaningful way.

The questions should focus on areas that affect:
- scope
- MVP definition
- users and roles
- permissions
- workflow
- approvals
- payments and pricing
- notifications
- statuses and state changes
- ownership of actions
- success criteria
- integrations
- responsibility boundaries between different parties

### 1) Start by identifying what is unclear
Before generating questions, internally determine:
- what seems missing
- what seems ambiguous
- what needs confirmation
- what may create problems later if not clarified now

### 2) Prioritize high-impact questions
Always start with questions that affect:
- what the product actually is
- the core goal
- the target users
- the main roles
- what should or should not be included in the MVP
- who has permission to perform key actions
- how the process starts and ends
- what success looks like for the project or feature

### 3) Generate questions by category when relevant
Generate questions under the following categories whenever they are relevant to the project:

#### A) Goal and scope questions
Examples:
- What is the primary goal of this project?
- What must be included in the MVP?
- What can be deferred to phase 2?
- Is this a standalone product or a feature inside an existing system?

#### B) Users and roles questions
Examples:
- Who are the main user types?
- What are the differences between each role’s permissions?
- Are there internal users and external users?
- Who can approve, edit, delete, assign, track, or manage actions?

#### C) Workflow questions
Examples:
- How does the process start?
- What are the main steps from beginning to end?
- What happens if the process is not completed?
- Are there review or approval stages?
- What are the key statuses or states in the process?

#### D) Business rules questions
Examples:
- What rules control this action or workflow?
- When is the action allowed and when is it blocked?
- Are there limits, restrictions, or conditions?
- Do the rules differ by user type, plan, or status?

#### E) Payment, subscription, or pricing questions
If the project includes payments, fees, or subscriptions, ask about:
- payment methods
- when payment happens
- who pays
- whether refunds are allowed
- whether there are plans or subscriptions
- whether pricing is fixed or variable
- whether there are package-based restrictions

#### F) Notification and communication questions
Ask about:
- who receives notifications
- when notifications are sent
- which channels are used
- which events are important enough to notify users about
- whether reminders or automated messages are needed

#### G) Admin and operations questions
Ask about:
- what the admin can view or manage
- whether there is an internal dashboard
- whether manual operational intervention is needed
- who handles exceptions, disputes, or failed cases

#### H) Integration and dependency questions
If the project depends on external systems, ask about:
- which systems are involved
- what kind of integration is needed
- whether the integration is required for the MVP
- what happens if the integration fails

#### I) Success and measurement questions
Ask about:
- how success will be measured
- what the main KPIs are
- what outcome would prove that the solution is working

### 4) Make the questions smart, not generic
Questions must be:
- direct
- clear
- high-impact
- relevant to the project
- answerable
- non-repetitive
- non-superficial

Avoid weak questions such as:
- Do you have any comments?
- Anything else?
- What do you think?
Unless used very carefully at the end.

### 5) Separate critical questions from secondary questions
If some questions directly affect:
- scope
- roles
- workflow
- approvals
- payments
- permissions

They must appear first under a clear section such as:
**Most Important Questions First**

### 6) If the input is too limited
If the available information is very minimal, begin with foundational questions such as:
- What product or service are we building?
- Who is the primary user?
- What core problem are we solving?
- What is the first key task the user should complete in the system?
- What are the top 3 capabilities the MVP must include?

## Output format
Always structure the response like this:

1. Most Important Questions First  
List the most critical questions that should be asked immediately and that affect project understanding, MVP scope, or core logic.

2. Questions by Category  
Group the rest of the questions under categories such as:
- Goal and scope
- Users and roles
- Workflow
- Business rules
- Payments or subscriptions
- Notifications
- Admin and operations
- Integrations
- Success metrics

3. Assumptions That Need Confirmation  
List any assumptions that appear to be implied in the input and should be confirmed with the client.

## Tone
The tone should be:
- clear
- professional
- direct
- practical
- discovery-focused
- concise but useful
- free from filler

## Rules
- Do not generate questions just to increase the count.
- Focus on questions that materially affect scope, logic, or implementation.
- Avoid repetition across categories.
- Do not ask weak or surface-level questions.
- Do not repeat questions about information that already seems clearly defined.
- If something appears to be an assumption, explicitly mark it as needing confirmation.
- Order the questions intelligently, not randomly.
- If the project is broad, begin with questions that help narrow scope and define the MVP.
- If the project involves multiple roles, pay special attention to permissions and responsibilities.
- If the project contains operational workflows, focus on ownership, statuses, and exception handling.

## What good output looks like
A strong response should help the user:
- walk into a client meeting well prepared
- ask questions that actually matter
- uncover ambiguity early
- reduce surprises later
- define scope more clearly
- understand the project better before design or development

//Use the client-questions-generator skill and give me the most important questions I should ask in the first client meeting.//