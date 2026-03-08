---
name: notebooklm
version: 1.0.0
description: Best practices and workflow patterns
---

# Best Practices

## Workflow Patterns

### Pattern 1: Research Session

```mermaid
stateDiagram-v2
    [*] --> CheckLib: notebook_manager.py list

    CheckLib --> ActivateNB: activate --id nb_docs
    ActivateNB --> BroadQ: Step 1 Broad question
    BroadQ --> AskBroad: ask_question.py overview
    AskBroad --> SpecificQ: Step 2 Specific questions

    SpecificQ --> Q1: ask_question.py specific Q1
    Q1 --> Q2: ask_question.py specific Q2
    Q2 --> Q3: ask_question.py specific Q3
    Q3 --> Synthesize: Step 3 Combine answers
    Synthesize --> [*]
```

---

### Pattern 2: Multi-Notebook Research

```mermaid
stateDiagram-v2
    [*] --> QueryNB1: ask_question.py --notebook-id nb_api
    QueryNB1 --> QueryNB2: ask_question.py --notebook-id nb_arch
    QueryNB2 --> QueryNB3: ask_question.py --notebook-id nb_changelog
    QueryNB3 --> CombineAnswers: Synthesize across notebooks
    CombineAnswers --> [*]
```

---
---
name: notebooklm
version: 1.0.0
description: Best practices for agent-led NotebookLM skill usage
---

# NotebookLM Skill Best Practices

This file focuses on how to use the skill well. The skill executes explicit NotebookLM operations. The agent stays responsible for selecting notebooks, asking follow-up questions, and synthesizing the final answer.

## Core Principle

Use NotebookLM for source-grounded retrieval from notebooks the user already prepared.

Do not use the skill as a substitute for planning, coding judgment, or broad open-ended research.

## Pattern 1: Broad Then Narrow

```mermaid
stateDiagram-v2
    [*] --> SelectNotebook: notebook_manager.py activate --id ...
    SelectNotebook --> AskOverview: ask_question.py broad overview
    AskOverview --> ReviewOverview

    ReviewOverview --> NextMove
    state NextMove <<choice>>
    NextMove --> AskDetail1: key area identified
    NextMove --> Stop: overview is enough

    AskDetail1 --> AskDetail2: ask targeted follow-up
    AskDetail2 --> Synthesize: agent combines results
    Stop --> [*]
    Synthesize --> [*]
```

Why it works:
- The first question maps the notebook before you spend more queries.
- Later questions can reference exact sections, features, or decisions.

## Pattern 2: Compare Multiple Notebooks

```mermaid
stateDiagram-v2
    [*] --> ActivateA: notebook_manager.py activate --id nb_a
    ActivateA --> QueryA: ask_question.py question for notebook A
    QueryA --> ActivateB: notebook_manager.py activate --id nb_b
    ActivateB --> QueryB: ask_question.py same question for notebook B
    QueryB --> Compare: agent compares outputs
    Compare --> [*]
```

Best use cases:
- Comparing APIs, policies, or architecture notes.
- Checking whether two sources describe the same workflow differently.

## Pattern 3: Register Before Relying On It

```mermaid
stateDiagram-v2
    [*] --> ReceiveURL
    ReceiveURL --> ClarifyMetadata
    ClarifyMetadata --> AddNotebook: notebook_manager.py add --url ...
    AddNotebook --> ActivateNotebook: notebook_manager.py activate --id ...
    ActivateNotebook --> FirstQuery: ask_question.py initial validation question
    FirstQuery --> [*]
```

Good validation questions:
- "What is this notebook mainly about?"
- "What kinds of sources appear in this notebook?"
- "What topics does this notebook cover most directly?"

## Question Strategy

```mermaid
stateDiagram-v2
    [*] --> PickQuestionType

    state PickQuestionType <<choice>>
    PickQuestionType --> Overview: need orientation
    PickQuestionType --> Extraction: need facts or lists
    PickQuestionType --> Comparison: need differences
    PickQuestionType --> Troubleshoot: need source-backed diagnosis

    Overview --> [*]
    Extraction --> [*]
    Comparison --> [*]
    Troubleshoot --> [*]
```

Prefer questions that are:
- Specific about the topic, feature, or decision.
- Narrow enough to answer from one notebook at a time.
- Explicit about expected output, such as list, summary, steps, or comparison.

Avoid questions that are:
- "Tell me everything about this notebook."
- "Solve this entire task for me."
- "Why did the authors think this way?" when the sources only show what they wrote.

## Anti-Patterns

| Avoid | Better Alternative |
|-------|--------------------|
| "Tell me everything." | "List the main sections and what each covers." |
| "Fix this code." | "What does the notebook say about implementing X?" |
| "Analyze all notebooks at once." | "Compare notebook A and notebook B on one topic." |
| "Keep asking until you know everything." | "Ask one follow-up per gap you can name." |

## Library Organization

```mermaid
stateDiagram-v2
    [*] --> ChooseScheme

    state ChooseScheme <<choice>>
    ChooseScheme --> ByProject
    ChooseScheme --> ByDomain
    ChooseScheme --> ByDocType

    ByProject --> SearchProject: notebook_manager.py search --query project-name
    ByDomain --> SearchDomain: notebook_manager.py search --query auth
    ByDocType --> SearchType: notebook_manager.py search --query api

    SearchProject --> [*]
    SearchDomain --> [*]
    SearchType --> [*]
```

Recommended metadata fields:
- `name`: short, recognizable notebook label.
- `description`: what the notebook contains.
- `topics`: searchable tags for later retrieval.

## Query Budget Management

```mermaid
stateDiagram-v2
    [*] --> CheckNeed

    state CheckNeed <<choice>>
    CheckNeed --> AskNow: notebook answer is required
    CheckNeed --> ReuseNotes: prior answer already covers it

    AskNow --> AskFocused: ask_question.py narrow question
    AskFocused --> SaveTakeaway: keep useful result locally
    SaveTakeaway --> [*]
    ReuseNotes --> [*]
```

To reduce unnecessary queries:
- Keep one notebook active when asking several related questions.
- Save useful answers in local notes instead of re-asking.
- Split large tasks into named sub-questions.

## Security And Local State

```mermaid
stateDiagram-v2
    [*] --> KeepLocal: data/ stays local
    KeepLocal --> IgnoreSensitive: do not commit auth or browser state
    IgnoreSensitive --> UseDedicatedAccount: recommended for automation
    UseDedicatedAccount --> [*]
```

Recommended safeguards:
- Keep `data/`, `.venv/`, and browser state out of version control.
- Prefer a dedicated Google account for automation workflows.
- Re-authenticate intentionally rather than sharing one profile across unrelated work.

## Agent + Skill Integration

```mermaid
stateDiagram-v2
    [*] --> UserTask
    UserTask --> DraftQuestion: agent drafts explicit NotebookLM query
    DraftQuestion --> QueryNotebook: ask_question.py --question ...
    QueryNotebook --> ReviewAnswer

    ReviewAnswer --> Decision
    state Decision <<choice>>
    Decision --> FollowUp: gap remains
    Decision --> UseResult: answer is sufficient

    FollowUp --> QueryNotebook
    UseResult --> FinalResponse: agent writes response or code
    FinalResponse --> [*]
```

The skill should be one step in a larger workflow, not the workflow owner.

## Practical Examples

```bash
:: Broad orientation
.\run.bat ask_question.py --question "Summarize the main topics covered in this notebook."

:: Targeted extraction
.\run.bat ask_question.py --question "List the authentication methods documented here."

:: Comparison setup
.\run.bat notebook_manager.py activate --id nb_arch
.\run.bat ask_question.py --question "What constraints are documented for deployment?"
```

