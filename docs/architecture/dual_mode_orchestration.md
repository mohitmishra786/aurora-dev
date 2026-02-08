# Aurora-Dev Architecture Diagrams

Comprehensive architecture documentation for the refactored AURORA-DEV multi-agent system.

---

## System Overview

```mermaid
graph TB
    subgraph "User Interfaces"
        CLI[CLI Interface]
        API[REST API]
        Dashboard[Web Dashboard]
    end
    
    subgraph "Orchestration Layer"
        DualModeOrch[DualModeOrchestrator]
        StateMachine[State Machine]
        Scheduler[Task Scheduler]
    end
    
    subgraph "Agent Layer"
        Architect[Architect Agent]
        Backend[Backend Agent]
        Frontend[Frontend Agent]
        QA[QA Agent]
        SelfCorrect[Self-Correction Loop]
    end
    
    subgraph "Execution & Security"
        DockerRunner[Docker Runner]
        SecuritySandbox[Security Sandbox]
        NetworkPolicy[Network Policy]
        SecretInjector[Secret Injector]
    end
    
    subgraph "Learning & Memory"
        Reflexion[Reflexion Engine]
        VectorStore[Vector Store]
        Redis[(Redis Cache)]
    end
    
    CLI --> DualModeOrch
    API --> DualModeOrch
    Dashboard --> API
    
    DualModeOrch --> StateMachine
    DualModeOrch --> Scheduler
    
    StateMachine --> Architect
    StateMachine --> Backend
    StateMachine --> Frontend
    StateMachine --> QA
    
    Backend --> SelfCorrect
    Frontend --> SelfCorrect
    
    SelfCorrect --> DockerRunner
    SelfCorrect --> Reflexion
    
    DockerRunner --> SecuritySandbox
    SecuritySandbox --> NetworkPolicy
    SecuritySandbox --> SecretInjector
    
    Reflexion --> VectorStore
    StateMachine --> Redis
    
    style DualModeOrch fill:#4CAF50
    style SecuritySandbox fill:#FF9800
    style Reflexion fill:#2196F3
```

---

## Dual-Mode Orchestration Flow

```mermaid
stateDiagram-v2
    [*] --> IDLE
    
    IDLE --> ModeSelection: Start Workflow
    
    state ModeSelection <<choice>>
    ModeSelection --> AutonomousFlow: mode=AUTONOMOUS
    ModeSelection --> CollaborativeFlow: mode=COLLABORATIVE
    
    state AutonomousFlow {
        [*] --> REQUIREMENTS
        REQUIREMENTS --> DESIGN
        DESIGN --> IMPLEMENTATION
        IMPLEMENTATION --> TESTING
        TESTING --> DEPLOYMENT
        DEPLOYMENT --> [*]
        
        DESIGN --> DESIGN: Auto-retry on failure
        IMPLEMENTATION --> IMPLEMENTATION: Self-correction
        TESTING --> IMPLEMENTATION: Test failures
    }
    
    state CollaborativeFlow {
        [*] --> REQUIREMENTS_C
        REQUIREMENTS_C --> DESIGN_C
        DESIGN_C --> AWAITING_APPROVAL: Breakpoint
        AWAITING_APPROVAL --> DESIGN_C: Rejected
        AWAITING_APPROVAL --> IMPLEMENTATION_C: Approved
        IMPLEMENTATION_C --> TESTING_C
        TESTING_C --> SECURITY_AUDIT
        SECURITY_AUDIT --> AWAITING_APPROVAL_2: Pre-deployment
        AWAITING_APPROVAL_2 --> DEPLOYMENT_C: Approved
        AWAITING_APPROVAL_2 --> SECURITY_AUDIT: Rejected
        DEPLOYMENT_C --> [*]
    }
    
    AutonomousFlow --> COMPLETED
    CollaborativeFlow --> COMPLETED
    
    AutonomousFlow --> FAILED: Max retries
    CollaborativeFlow --> CANCELLED: User cancels
    
    COMPLETED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
    
    note right of AWAITING_APPROVAL
        Human reviews design
        Can approve/reject
        Can provide feedback
    end note
    
    note right of AWAITING_APPROVAL_2
        Final security review
        before production
    end note
```

---

## Human-in-the-Loop Approval Workflow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant API
    participant Orchestrator
    participant StateMachine
    participant Agent
    participant Redis
    
    User->>CLI: aurora run --mode collaborative
    CLI->>API: POST /workflows (mode=collaborative)
    API->>Orchestrator: execute(workflow_id)
    Orchestrator->>StateMachine: transition(REQUIREMENTS)
    StateMachine->>Agent: execute_task()
    Agent-->>StateMachine: task_result
    
    StateMachine->>StateMachine: transition(DESIGN)
    Agent->>Agent: generate_design()
    Agent-->>StateMachine: design_complete
    
    StateMachine->>StateMachine: Check breakpoint
    StateMachine->>StateMachine: transition(AWAITING_APPROVAL)
    StateMachine->>Redis: save_paused_state()
    
    Orchestrator-->>API: ExecutionResult(paused=true)
    API-->>CLI: 200 OK (status: awaiting_approval)
    
    CLI->>User: ⏸️  Workflow paused for review
    
    User->>CLI: aurora pending
    CLI->>API: GET /workflows/pending-approvals
    API-->>CLI: [{workflow_id, phase, context}]
    
    User->>CLI: aurora approve <workflow_id>
    CLI->>API: POST /workflows/{id}/approval
    API->>Orchestrator: approve(workflow_id, reviewer_id)
    Orchestrator->>StateMachine: resume_workflow()
    StateMachine->>Redis: load_paused_state()
    StateMachine->>StateMachine: transition(IMPLEMENTATION)
    
    StateMachine->>Agent: execute_task()
    Agent-->>StateMachine: implementation_complete
    
    Orchestrator-->>API: ExecutionResult(status=running)
    API-->>CLI: 200 OK
    CLI-->>User: Workflow resumed
```

---

## Self-Correction Loop

```mermaid
flowchart TD
    Start([Task Input]) --> Generate[Generate Code]
    Generate --> Write[Write to Filesystem]
    Write --> SyntaxCheck{Syntax Valid?}
    
    SyntaxCheck -->|No| Reflect1[Generate Reflection]
    Reflect1 --> CheckAttempts1{Max Attempts?}
    CheckAttempts1 -->|No| Generate
    CheckAttempts1 -->|Yes| Failed([Failed])
    
    SyntaxCheck -->|Yes| RunTests[Run Tests in Sandbox]
    RunTests --> TestPass{Tests Pass?}
    
    TestPass -->|No| Reflect2[Generate Reflection]
    Reflect2 --> CheckAttempts2{Max Attempts?}
    CheckAttempts2 -->|No| Generate
    CheckAttempts2 -->|Yes| Failed
    
    TestPass -->|Yes| QualityCheck{Quality >= Threshold?}
    QualityCheck -->|No| Reflect3[Generate Reflection]
    Reflect3 --> CheckAttempts3{Max Attempts?}
    CheckAttempts3 -->|No| Generate
    CheckAttempts3 -->|Yes| Failed
    
    QualityCheck -->|Yes| StoreMemory[Store in Episodic Memory]
    StoreMemory --> Success([Success])
    
    style Generate fill:#4CAF50
    style RunTests fill:#2196F3
    style Reflect1 fill:#FF9800
    style Reflect2 fill:#FF9800
    style Reflect3 fill:#FF9800
    style Success fill:#4CAF50
    style Failed fill:#f44336
```

---

## Security Sandbox Architecture

```mermaid
graph TB
    subgraph "Application Layer"
        Agent[Agent Code]
        SelfCorrection[Self-Correction Loop]
    end
    
    subgraph "Sandbox Layer"
        SecureSandbox[Secure Sandbox]
        
        subgraph "Security Policies"
            NetworkPolicy[Network Policy]
            ResourceLimits[Resource Limits]
            SecretInjector[Secret Injector]
        end
        
        subgraph "Policy Enforcement"
            IPTables[iptables Rules]
            CGroups[cgroups Limits]
            TmpfsSecrets[tmpfs Secret Mount]
        end
    end
    
    subgraph "Container Runtime"
        Docker[Docker Engine]
        
        subgraph "Container"
            IsolatedNetwork[Isolated Network]
            LimitedResources[Limited Resources]
            ReadOnlyFS[Read-Only FS]
            SecretFiles[Secret Files]
        end
    end
    
    Agent --> SelfCorrection
    SelfCorrection --> SecureSandbox
    
    SecureSandbox --> NetworkPolicy
    SecureSandbox --> ResourceLimits
    SecureSandbox --> SecretInjector
    
    NetworkPolicy --> IPTables
    ResourceLimits --> CGroups
    SecretInjector --> TmpfsSecrets
    
    IPTables --> Docker
    CGroups --> Docker
    TmpfsSecrets --> Docker
    
    Docker --> IsolatedNetwork
    Docker --> LimitedResources
    Docker --> ReadOnlyFS
    Docker --> SecretFiles
    
    style NetworkPolicy fill:#FF9800
    style ResourceLimits fill:#FF9800
    style SecretInjector fill:#FF9800
    style IsolatedNetwork fill:#4CAF50
    style LimitedResources fill:#4CAF50
    style ReadOnlyFS fill:#4CAF50
```

### Network Policy Details

```mermaid
graph LR
    Container[Container] --> NetCheck{Network Policy}
    
    NetCheck -->|ISOLATED| Block[Block All]
    NetCheck -->|INTERNAL| Internal[Internal Only]
    NetCheck -->|RESTRICTED| Whitelist{Check Whitelist}
    NetCheck -->|NONE| Allow[Allow]
    
    Whitelist -->|pypi.org| AllowPyPI[Allow]
    Whitelist -->|npmjs.org| AllowNPM[Allow]
    Whitelist -->|github.com| AllowGitHub[Allow]
    Whitelist -->|Other| BlockOther[Block]
    
    style Block fill:#f44336
    style AllowPyPI fill:#4CAF50
    style AllowNPM fill:#4CAF50
    style AllowGitHub fill:#4CAF50
    style BlockOther fill:#f44336
```

---

## CLI and API Integration

```mermaid
graph TB
    subgraph "User Layer"
        User[User]
    end
    
    subgraph "CLI Commands"
        RunCmd[aurora run]
        ApproveCmd[aurora approve]
        PendingCmd[aurora pending]
        PauseCmd[aurora pause]
        ResumeCmd[aurora resume]
    end
    
    subgraph "API Endpoints"
        StartWF[POST /workflows]
        GetGraph[GET /workflows/:id/graph]
        PostApproval[POST /workflows/:id/approval]
        GetPending[GET /workflows/pending-approvals]
        PostPause[POST /workflows/:id/pause]
        PostResume[POST /workflows/:id/resume]
    end
    
    subgraph "Backend Services"
        DualModeOrch[DualModeOrchestrator]
        StateMachine[State Machine]
        Redis[(Redis)]
    end
    
    User --> RunCmd
    User --> ApproveCmd
    User --> PendingCmd
    User --> PauseCmd
    User --> ResumeCmd
    
    RunCmd --> StartWF
    ApproveCmd --> PostApproval
    PendingCmd --> GetPending
    PauseCmd --> PostPause
    ResumeCmd --> PostResume
    
    StartWF --> DualModeOrch
    GetGraph --> StateMachine
    PostApproval --> DualModeOrch
    GetPending --> StateMachine
    PostPause --> StateMachine
    PostResume --> StateMachine
    
    StateMachine --> Redis
    
    style RunCmd fill:#4CAF50
    style ApproveCmd fill:#2196F3
    style PendingCmd fill:#FF9800
```

---

## Data Flow: Code Generation with Self-Correction

```mermaid
sequenceDiagram
    participant Orchestrator
    participant BackendAgent
    participant SelfCorrection
    participant Sandbox
    participant Reflexion
    participant Redis
    
    Orchestrator->>BackendAgent: implement_endpoint(task)
    BackendAgent->>SelfCorrection: run(generator_func)
    
    loop Until Success or Max Attempts
        SelfCorrection->>SelfCorrection: generate_code()
        SelfCorrection->>SelfCorrection: write_to_filesystem()
        SelfCorrection->>SelfCorrection: check_syntax()
        
        alt Syntax Error
            SelfCorrection->>Reflexion: generate_reflection(VALIDATION_ERROR)
        else Syntax OK
            SelfCorrection->>Sandbox: run_tests()
            Sandbox->>Sandbox: Docker container execution
            Sandbox-->>SelfCorrection: test_results
            
            alt Tests Failed
                SelfCorrection->>Reflexion: generate_reflection(TEST_FAILURE)
            else Tests Passed
                SelfCorrection->>SelfCorrection: check_quality()
                
                alt Quality Low
                    SelfCorrection->>Reflexion: generate_reflection(PERFORMANCE)
                else Quality Good
                    SelfCorrection->>Reflexion: store_success()
                end
            end
        end
        
        Reflexion->>Redis: store_reflection()
        Reflexion-->>SelfCorrection: retry_context
    end
    
    SelfCorrection-->>BackendAgent: final_code
    BackendAgent-->>Orchestrator: AgentResponse
```
