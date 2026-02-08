/**
 * Aurora-Dev API Client
 * 
 * TypeScript client for interacting with the Aurora-Dev backend API.
 * Used by the React Dashboard for workflow visualization and approvals.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// =============================================================================
// Types
// =============================================================================

export interface AgentOutput {
    agent_name: string;
    output_type: string;
    content: any;
    generated_at: string;
}

export interface BreakpointDetails {
    checkpoint_name: string;
    reason: string;
    context: Record<string, any>;
    requires_approval: boolean;
}

export interface ApprovalRecord {
    approved: boolean;
    reviewer_id: string;
    comments?: string;
    decided_at: string;
}

export interface WorkflowState {
    workflow_id: string;
    project_id: string;
    status: 'starting' | 'running' | 'paused' | 'awaiting_approval' | 'completed' | 'failed' | 'cancelled';
    current_phase: string;
    agent_output?: AgentOutput;
    breakpoint?: BreakpointDetails;
    approvals: ApprovalRecord[];
    progress_percent: number;
    phase_results: Record<string, any>;
    started_at: string;
    updated_at: string;
}

export interface ApprovalRequest {
    approved: boolean;
    reviewer_id: string;
    comments?: string;
    modifications?: Record<string, any>;
}

export interface ApprovalResponse {
    workflow_id: string;
    status: 'resumed' | 'rejected';
    message: string;
    resumed_at?: string;
}

export interface PendingApprovalItem {
    workflow_id: string;
    project_id: string;
    current_phase: string;
    checkpoint?: string;
    paused_at: string;
    task_description: string;
}

export interface PendingApprovalsResponse {
    pending: PendingApprovalItem[];
    total: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Fetch the full state of a workflow.
 * 
 * Used by the dashboard to populate the Decision Modal
 * when status === 'awaiting_approval'.
 */
export async function getWorkflowState(workflowId: string): Promise<WorkflowState> {
    const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/state`);

    if (!response.ok) {
        throw new Error(`Failed to fetch workflow state: ${response.status}`);
    }

    return response.json();
}

/**
 * Approve a paused workflow.
 * 
 * Resumes execution from the breakpoint.
 * 
 * @param workflowId - ID of the workflow to approve
 * @param reviewerId - ID of the approving user
 * @param comments - Optional review comments
 */
export async function approveWorkflow(
    workflowId: string,
    reviewerId: string,
    comments?: string,
): Promise<ApprovalResponse> {
    const request: ApprovalRequest = {
        approved: true,
        reviewer_id: reviewerId,
        comments,
    };

    const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`Failed to approve workflow: ${response.status}`);
    }

    return response.json();
}

/**
 * Reject a paused workflow.
 * 
 * Cancels the workflow with the provided reason.
 * 
 * @param workflowId - ID of the workflow to reject
 * @param reviewerId - ID of the rejecting user
 * @param reason - Reason for rejection
 */
export async function rejectWorkflow(
    workflowId: string,
    reviewerId: string,
    reason: string,
): Promise<ApprovalResponse> {
    const request: ApprovalRequest = {
        approved: false,
        reviewer_id: reviewerId,
        comments: reason,
    };

    const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        throw new Error(`Failed to reject workflow: ${response.status}`);
    }

    return response.json();
}

/**
 * List all workflows awaiting approval.
 * 
 * Used to populate the pending approvals list in the dashboard.
 */
export async function getPendingApprovals(
    projectId?: string,
): Promise<PendingApprovalsResponse> {
    const url = new URL(`${API_BASE_URL}/workflows/pending-approvals`);
    if (projectId) {
        url.searchParams.set('project_id', projectId);
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
        throw new Error(`Failed to fetch pending approvals: ${response.status}`);
    }

    return response.json();
}

/**
 * Pause a running workflow.
 * 
 * @param workflowId - ID of the workflow to pause
 * @param reason - Optional reason for pausing
 */
export async function pauseWorkflow(
    workflowId: string,
    reason?: string,
): Promise<{ message: string; paused_at: string }> {
    const url = new URL(`${API_BASE_URL}/workflows/${workflowId}/pause`);
    if (reason) {
        url.searchParams.set('reason', reason);
    }

    const response = await fetch(url.toString(), {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to pause workflow: ${response.status}`);
    }

    return response.json();
}

/**
 * Resume a paused workflow (admin override).
 * 
 * @param workflowId - ID of the workflow to resume
 */
export async function resumeWorkflow(
    workflowId: string,
): Promise<{ message: string; resumed_at: string }> {
    const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/resume`, {
        method: 'POST',
    });

    if (!response.ok) {
        throw new Error(`Failed to resume workflow: ${response.status}`);
    }

    return response.json();
}

// =============================================================================
// Polling Hook Helper
// =============================================================================

/**
 * Create a polling function for workflow state.
 * 
 * Usage:
 * ```typescript
 * const poller = createStatePoller(workflowId, (state) => {
 *   setWorkflowState(state);
 *   if (state.status === 'awaiting_approval') {
 *     setShowModal(true);
 *   }
 * });
 * 
 * poller.start();
 * // Later...
 * poller.stop();
 * ```
 */
export function createStatePoller(
    workflowId: string,
    onState: (state: WorkflowState) => void,
    intervalMs: number = 2000,
) {
    let intervalId: NodeJS.Timeout | null = null;

    return {
        start: async () => {
            // Initial fetch
            try {
                const state = await getWorkflowState(workflowId);
                onState(state);
            } catch (error) {
                console.error('Initial state fetch failed:', error);
            }

            // Start polling
            intervalId = setInterval(async () => {
                try {
                    const state = await getWorkflowState(workflowId);
                    onState(state);
                } catch (error) {
                    console.error('State poll failed:', error);
                }
            }, intervalMs);
        },

        stop: () => {
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
        },
    };
}
