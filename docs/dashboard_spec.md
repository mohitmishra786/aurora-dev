# Aurora-Dev Dashboard Technical Specification

React/Next.js dashboard for workflow visualization and human-in-the-loop approvals.

---

## Overview

The dashboard provides real-time visibility into workflow execution and enables human reviewers to approve or reject agent outputs at configured breakpoints.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Dashboard (Next.js)                  │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Workflow   │  │   Pending   │  │    Decision     │ │
│  │    List     │  │  Approvals  │  │     Modal       │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────┤
│                 API Client (api_client.ts)              │
├─────────────────────────────────────────────────────────┤
│         Polling (2s) / WebSocket (preferred)            │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend                         │
├─────────────────────────────────────────────────────────┤
│  GET  /api/v1/workflows/{id}/state                      │
│  POST /api/v1/workflows/{id}/approval                   │
│  GET  /api/v1/workflows/pending-approvals               │
│  WS   /ws/workflows/{id}                                │
└─────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. WorkflowStatePoller

Polls `GET /api/v1/workflows/{id}/state` every 2 seconds.

```typescript
// Pseudo-code
useEffect(() => {
  const interval = setInterval(async () => {
    const state = await getWorkflowState(workflowId);
    setWorkflowState(state);
    
    if (state.status === 'awaiting_approval') {
      setShowDecisionModal(true);
    }
  }, 2000);
  
  return () => clearInterval(interval);
}, [workflowId]);
```

### 2. Decision Modal

Displays when `status === 'awaiting_approval'`.

**Content:**
- Agent name and output type
- Full agent output (Architecture Plan, Code, etc.)
- Breakpoint reason and context
- Approve/Reject buttons

**Actions:**
- **Approve**: `POST /approval` with `approved: true`
- **Reject**: `POST /approval` with `approved: false` + reason

### 3. Workflow List

Shows all workflows with status indicators:
- 🟢 Running
- 🟡 Awaiting Approval
- 🔴 Failed
- ✅ Completed

---

## API Integration

### Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/workflows/{id}/state` | GET | Get full state for modal |
| `/workflows/{id}/approval` | POST | Submit approval/rejection |
| `/workflows/pending-approvals` | GET | List awaiting workflows |
| `/ws/workflows/{id}` | WebSocket | Real-time updates (optional) |

### Data Types

```typescript
interface WorkflowState {
  workflow_id: string;
  project_id: string;
  status: 'running' | 'paused' | 'awaiting_approval' | 'completed' | 'failed';
  current_phase: string;
  agent_output?: AgentOutput;
  breakpoint?: BreakpointDetails;
  approvals: ApprovalRecord[];
  progress_percent: number;
  started_at: string;
  updated_at: string;
}

interface AgentOutput {
  agent_name: string;
  output_type: string;
  content: any;
  generated_at: string;
}

interface BreakpointDetails {
  checkpoint_name: string;
  reason: string;
  context: Record<string, any>;
  requires_approval: boolean;
}
```

---

## Decision Modal Behavior

### When `status === 'awaiting_approval'`

1. Modal opens automatically
2. Displays `agent_output.content` formatted by type:
   - `architecture_plan`: Render as JSON tree or Mermaid diagram
   - `code`: Syntax-highlighted code block
   - `user_stories`: Formatted list
3. Shows breakpoint context
4. Provides Approve/Reject buttons

### Approve Flow

```typescript
async function handleApprove(comments?: string) {
  await approveWorkflow(workflowId, reviewerId, comments);
  setShowDecisionModal(false);
  // Polling will pick up resumed state
}
```

### Reject Flow

```typescript
async function handleReject(reason: string) {
  await rejectWorkflow(workflowId, reason);
  setShowDecisionModal(false);
  // Workflow will show as cancelled
}
```

---

## File Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx              # Main dashboard
│   │   └── workflows/
│   │       └── page.tsx          # Workflow list
│   ├── components/
│   │   ├── DecisionModal.tsx     # Approval modal
│   │   ├── WorkflowCard.tsx      # Single workflow card
│   │   └── AgentOutputViewer.tsx # Render agent output
│   └── lib/
│       ├── api_client.ts         # API functions
│       └── useWebSocket.ts       # WebSocket hook
```

---

## Implementation Priority

1. **P0**: `api_client.ts` - API client functions
2. **P0**: Decision Modal with approve/reject
3. **P1**: Workflow list with status indicators
4. **P2**: WebSocket integration for live updates
5. **P2**: Agent output visualization components
