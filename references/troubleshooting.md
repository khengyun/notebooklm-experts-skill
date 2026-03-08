# NotebookLM Skill Troubleshooting

This file is for diagnosing failures in the local skill workflow. It does not describe an MCP server or standalone hosted service. In most cases, the fix is to restore local execution, authentication, browser state, or notebook selection.

## Error Decision Tree

```mermaid
stateDiagram-v2
    [*] --> ObserveFailure

    ObserveFailure --> IdentifyClass
    state IdentifyClass <<choice>>
    IdentifyClass --> WrapperIssue: command run directly
    IdentifyClass --> AuthIssue: login or session problem
    IdentifyClass --> BrowserIssue: Chrome or automation problem
    IdentifyClass --> NotebookIssue: notebook lookup or access problem
    IdentifyClass --> RateLimitIssue: NotebookLM quota reached

    WrapperIssue --> UseWrapper: switch to .\run.bat or ./run.sh
    UseWrapper --> [*]

    AuthIssue --> AuthFlow
    BrowserIssue --> BrowserFlow
    NotebookIssue --> NotebookFlow
    RateLimitIssue --> RateFlow

    AuthFlow --> [*]
    BrowserFlow --> [*]
    NotebookFlow --> [*]
    RateFlow --> [*]
```

## Auth Problems

```mermaid
stateDiagram-v2
    [*] --> CheckAuthStatus: auth_manager.py status

    CheckAuthStatus --> AuthState
    state AuthState <<choice>>
    AuthState --> FirstSetup: never authenticated
    AuthState --> Reauth: session expired or stale
    AuthState --> CorrectAccount: wrong Google account active

    FirstSetup --> VisibleLogin: auth_manager.py setup
    VisibleLogin --> [*]

    Reauth --> RefreshSession: auth_manager.py reauth
    RefreshSession --> [*]

    CorrectAccount --> ClearAndSetup: clear or switch profile, then setup
    ClearAndSetup --> [*]

    note right of VisibleLogin
        Keep the browser visible so the user
        can complete sign-in manually.
    end note
```

Common commands:

```bat
.\run.bat auth_manager.py status
.\run.bat auth_manager.py setup
.\run.bat auth_manager.py reauth
```

## Browser Problems

```mermaid
stateDiagram-v2
    [*] --> BrowserFailure

    BrowserFailure --> BrowserCase
    state BrowserCase <<choice>>
    BrowserCase --> MissingChrome: Chrome not installed for patchright
    BrowserCase --> CrashedState: browser crashes or hangs
    BrowserCase --> StaleSession: browser state is corrupted

    MissingChrome --> InstallChrome: python install.py or patchright install chrome
    InstallChrome --> [*]

    CrashedState --> CleanupState: cleanup_manager.py --preserve-library
    CleanupState --> RetryAuthOrQuery
    RetryAuthOrQuery --> [*]

    StaleSession --> ReauthAfterCleanup: cleanup then auth_manager.py reauth
    ReauthAfterCleanup --> [*]
```

Checks to perform:
- Confirm Google Chrome is available, not only Chromium.
- Re-run through the wrapper instead of invoking script modules directly.
- Clean browser state before attempting a fresh auth flow.

## Notebook Selection Or Access Problems

```mermaid
stateDiagram-v2
    [*] --> NotebookFailure

    NotebookFailure --> NotebookCase
    state NotebookCase <<choice>>
    NotebookCase --> MissingNotebook: notebook not registered locally
    NotebookCase --> WrongActive: wrong notebook is active
    NotebookCase --> AccessDenied: shared URL or account mismatch

    MissingNotebook --> ListLibrary: notebook_manager.py list
    ListLibrary --> AddNotebook: notebook_manager.py add --url ...
    AddNotebook --> [*]

    WrongActive --> ActivateCorrect: notebook_manager.py activate --id ...
    ActivateCorrect --> [*]

    AccessDenied --> CheckURLAndAccount
    CheckURLAndAccount --> ReaddOrReauth
    ReaddOrReauth --> [*]
```

Useful commands:

```bat
.\run.bat notebook_manager.py list
.\run.bat notebook_manager.py add --url URL
.\run.bat notebook_manager.py activate --id NOTEBOOK_ID
```

## Rate Limit Problems

```mermaid
stateDiagram-v2
    [*] --> HitLimit

    HitLimit --> ChooseResponse
    state ChooseResponse <<choice>>
    ChooseResponse --> WaitAndRetry: defer work until quota resets
    ChooseResponse --> ReduceQueries: ask fewer, narrower questions
    ChooseResponse --> ChangeAccount: switch to another prepared profile

    WaitAndRetry --> [*]
    ReduceQueries --> [*]
    ChangeAccount --> [*]
```

When rate limited:
- Prefer fewer, higher-value questions.
- Reuse prior answers when possible.
- Switch profiles only if that is already part of your normal setup.

## Full Recovery Flow

```mermaid
stateDiagram-v2
    [*] --> BackupLocalData
    BackupLocalData --> CleanupState: cleanup_manager.py --confirm --force
    CleanupState --> RebuildEnv: recreate .venv if needed
    RebuildEnv --> SetupAuth: auth_manager.py setup
    SetupAuth --> RestoreLibrary: import or restore notebook metadata
    RestoreLibrary --> VerifyFlow
    VerifyFlow --> [*]
```

Safer partial recovery:

```bat
:: Recreate local environment but keep library data if you have backed it up
python install.py
.\run.bat auth_manager.py status
```

## Error Reference

| Symptom | Likely Cause | Recommended Action |
|---------|--------------|--------------------|
| `ModuleNotFoundError` | script bypassed the local environment | use `.\run.bat` |
| auth expired | saved session is no longer valid | run `auth_manager.py reauth` |
| browser launch failure | missing Chrome or stale browser state | reinstall Chrome or clean state |
| notebook not found | notebook is not in local library | run `notebook_manager.py list` or `add` |
| answer comes from wrong notebook | wrong active notebook | run `notebook_manager.py activate --id ...` |

## Prevention Tips

1. Always use `run.bat` or `run.sh` instead of calling scripts directly.
2. Keep notebook metadata organized so activation mistakes are rare.
3. Use a dedicated account if browser automation policies are strict.
4. Back up or export your notebook library before destructive cleanup.
5. Treat cleanup as a local repair step, not a normal daily workflow.

## Minimal Diagnostic Bundle

When reporting an issue, collect:

```bat
.\run.bat auth_manager.py status
.\run.bat notebook_manager.py list
.\run.bat debug_skill.py
```

Add a short note saying whether the failure is:
- before login,
- during browser automation,
- during notebook selection, or
- after the question is submitted.
