# NotebookLM Skill Usage Patterns

This file collects procedural workflow patterns for using the NotebookLM skill. These patterns are agent-led: the skill executes explicit actions, and the agent decides what to ask next.

## Pattern 1: Initial Setup Workflow

```mermaid
stateDiagram-v2
    [*] --> CheckAuth: auth_manager.py status

    CheckAuth --> AuthState
    state AuthState <<choice>>
    AuthState --> Ready: authenticated
    AuthState --> NeedSetup: not authenticated

    NeedSetup --> Login: auth_manager.py setup
    Login --> Ready

    Ready --> AddNotebook: notebook_manager.py add --url ...
    AddNotebook --> ActivateNotebook: notebook_manager.py activate --id ...
    ActivateNotebook --> [*]: ready to query

    note right of Login
        Browser should stay visible
        so the user can sign in
    end note
```

---

## Pattern 2: Notebook Registration Workflow

```mermaid
stateDiagram-v2
    [*] --> UserSharesURL

    UserSharesURL --> ChooseMetadataMode
    state ChooseMetadataMode <<choice>>
    ChooseMetadataMode --> AutoDetect: use metadata fetch
    ChooseMetadataMode --> AskUser: ask for explicit metadata

    AutoDetect --> AddNotebook: notebook_manager.py add --url ...
    AskUser --> AddWithFields: notebook_manager.py add --url ... --name ... --description ... --topics ...

    AddNotebook --> ActivateNotebook
    AddWithFields --> ActivateNotebook
    ActivateNotebook --> [*]

    note right of AutoDetect
        Use the library workflow to infer
        metadata when available
    end note
```

---

## Pattern 3: Daily Query Workflow

```mermaid
stateDiagram-v2
    [*] --> CheckLibrary: notebook_manager.py list
    CheckLibrary --> SelectNotebook: choose active or specific notebook
    SelectNotebook --> AskQuestion: ask_question.py --question ...
    AskQuestion --> ReviewAnswer

    ReviewAnswer --> Completeness
    state Completeness <<choice>>
    Completeness --> FollowUp: more detail needed
    Completeness --> [*]: answer set is sufficient

    FollowUp --> AskQuestion: ask a narrower follow-up
```

---

## Pattern 4: Follow-Up Workflow

```mermaid
stateDiagram-v2
    [*] --> AskInitial: ask_question.py --question ...
    AskInitial --> ReviewAnswer

    ReviewAnswer --> GapCheck
    state GapCheck <<choice>>
    GapCheck --> AskFollowUp: gaps remain
    GapCheck --> Synthesize: enough information

    AskFollowUp --> ReviewAnswer: ask another explicit question
    Synthesize --> Respond: agent writes final answer
    Respond --> [*]

    note right of ReviewAnswer
        The agent decides whether the
        NotebookLM answer is complete
    end note
```

---

## Pattern 5: Multi-Notebook Comparison Workflow

```mermaid
stateDiagram-v2
    [*] --> ActivateNB1: notebook_manager.py activate --id nb1
    ActivateNB1 --> QueryNB1: ask_question.py --question ...
    QueryNB1 --> ActivateNB2: notebook_manager.py activate --id nb2
    ActivateNB2 --> QueryNB2: ask_question.py --question ...
    QueryNB2 --> CompareResults: agent compares answers
    CompareResults --> [*]
```

---

## Pattern 6: Error Recovery Workflow

```mermaid
stateDiagram-v2
    [*] --> IdentifyError

    state IdentifyError <<choice>>
    IdentifyError --> AuthIssue: auth problem
    IdentifyError --> BrowserIssue: browser problem
    IdentifyError --> RateLimit: rate limited

    AuthIssue --> CheckStatus: auth_manager.py status
    CheckStatus --> Reauth: auth_manager.py reauth
    Reauth --> [*]

    BrowserIssue --> Cleanup: cleanup_manager.py --preserve-library
    Cleanup --> Retry: rerun auth or query command
    Retry --> [*]

    RateLimit --> WaitOrSwitch
    state WaitOrSwitch <<choice>>
    WaitOrSwitch --> Wait: pause and retry later
    WaitOrSwitch --> SwitchProfile: auth_manager.py set-active --id ...
    Wait --> [*]
    SwitchProfile --> [*]
```

---

## Pattern 7: Batch Query Workflow

```mermaid
stateDiagram-v2
    [*] --> PrepareQuestions
    PrepareQuestions --> NextQuestion
    NextQuestion --> AskQuestion: ask_question.py --question ... --notebook-id ...
    AskQuestion --> Delay: short pause

    Delay --> Remaining
    state Remaining <<choice>>
    Remaining --> NextQuestion: more questions remain
    Remaining --> [*]: batch complete
```

---

## Pattern 8: Notebook Organization Workflow

```mermaid
stateDiagram-v2
    [*] --> ChooseGrouping

    state ChooseGrouping <<choice>>
    ChooseGrouping --> ByProject: project-focused topics
    ChooseGrouping --> ByDomain: domain-focused topics
    ChooseGrouping --> ByType: document-type tags

    ByProject --> SearchProject: notebook_manager.py search --query ...
    ByDomain --> SearchDomain: notebook_manager.py search --query ...
    ByType --> SearchType: notebook_manager.py search --query ...

    SearchProject --> [*]
    SearchDomain --> [*]
    SearchType --> [*]
```

---

## Pattern 9: Library Maintenance Workflow

```mermaid
stateDiagram-v2
    [*] --> RegisterNotebook: notebook_manager.py add --url ...
    RegisterNotebook --> ListNotebooks: notebook_manager.py list
    ListNotebooks --> SetActive: notebook_manager.py activate --id ...
    SetActive --> DefaultQuery: ask_question.py --question ...
    DefaultQuery --> OverrideQuery: ask_question.py --question ... --notebook-id ...
    OverrideQuery --> [*]
```

---

## Copilot Workflow: User Shares URL

```mermaid
stateDiagram-v2
    [*] --> DetectNotebookURL
    DetectNotebookURL --> CheckLibrary: notebook_manager.py list

    CheckLibrary --> KnownState
    state KnownState <<choice>>
    KnownState --> RegisterNotebook: URL not present
    KnownState --> QueryNotebook: URL already known

    RegisterNotebook --> AddNotebook: notebook_manager.py add --url ...
    AddNotebook --> ActivateNotebook: notebook_manager.py activate --id ...
    ActivateNotebook --> QueryNotebook
    QueryNotebook --> [*]
```

---

## Copilot Workflow: Query and Synthesis

```mermaid
stateDiagram-v2
    [*] --> UnderstandTask
    UnderstandTask --> DraftQuestion: formulate explicit NotebookLM question
    DraftQuestion --> AskQuestion: ask_question.py --question ...
    AskQuestion --> ReviewAnswer

    ReviewAnswer --> NextStep
    state NextStep <<choice>>
    NextStep --> AskFollowUp: more NotebookLM detail needed
    NextStep --> Synthesize: answer set is sufficient

    AskFollowUp --> AskQuestion
    Synthesize --> ImplementOrReply: agent continues with implementation or response
    ImplementOrReply --> [*]
```

---

## Quick Reference

```bat
:: Always use the wrapper
.\run.bat [script].py [args]

:: Common operations
.\run.bat auth_manager.py status
.\run.bat auth_manager.py setup --name "My Account"
.\run.bat notebook_manager.py list
.\run.bat notebook_manager.py add --url URL
.\run.bat ask_question.py --question "..."
.\run.bat cleanup_manager.py --preserve-library
```

Use these patterns when the task is procedural. Use `references/best-practices.md` for question quality, anti-patterns, and broader guidance.
