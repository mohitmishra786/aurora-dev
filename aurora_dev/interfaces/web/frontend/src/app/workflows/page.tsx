"use client";

import { useState, useEffect, useCallback } from "react";
import { useWorkflowWebSocket, WorkflowEvent } from "@/lib/useWebSocket";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

interface Workflow {
    id: string;
    project_id: string;
    status: 'running' | 'paused' | 'awaiting_approval' | 'completed' | 'failed' | 'cancelled';
    phase: string;
    mode: 'autonomous' | 'collaborative';
    started_at: string;
    updated_at: string;
}

interface PendingApproval {
    workflow_id: string;
    approval_id: string;
    phase: string;
    context: {
        agent: string;
        description: string;
        outputs: Record<string, unknown>;
    };
    requested_at: string;
}

// Mock data for when API is unavailable
const mockWorkflows: Workflow[] = [
    { id: 'wf-001', project_id: 'proj-1', status: 'running', phase: 'implementation', mode: 'autonomous', started_at: '2026-02-08T10:00:00Z', updated_at: '2026-02-08T13:30:00Z' },
    { id: 'wf-002', project_id: 'proj-2', status: 'awaiting_approval', phase: 'design', mode: 'collaborative', started_at: '2026-02-08T09:00:00Z', updated_at: '2026-02-08T12:00:00Z' },
    { id: 'wf-003', project_id: 'proj-1', status: 'completed', phase: 'completed', mode: 'autonomous', started_at: '2026-02-07T14:00:00Z', updated_at: '2026-02-07T18:00:00Z' },
    { id: 'wf-004', project_id: 'proj-3', status: 'paused', phase: 'testing', mode: 'collaborative', started_at: '2026-02-08T11:00:00Z', updated_at: '2026-02-08T14:00:00Z' },
];

const mockPendingApprovals: PendingApproval[] = [
    {
        workflow_id: 'wf-002',
        approval_id: 'apr-001',
        phase: 'design',
        context: {
            agent: 'Architect',
            description: 'System architecture design complete - awaiting review',
            outputs: { diagram: 'architecture.md', decisions: ['microservices', 'postgresql'] },
        },
        requested_at: '2026-02-08T12:00:00Z',
    },
];

// Phase visualization colors
const phaseColors: Record<string, string> = {
    idle: '#6366f1',
    requirements: '#8b5cf6',
    design: '#a855f7',
    implementation: '#ec4899',
    testing: '#f43f5e',
    code_review: '#f97316',
    security_audit: '#eab308',
    documentation: '#84cc16',
    deployment: '#22c55e',
    monitoring: '#14b8a6',
    paused: '#6b7280',
    awaiting_approval: '#f59e0b',
    completed: '#10b981',
    failed: '#ef4444',
    cancelled: '#9ca3af',
};

// Phase order for visualization
const phaseOrder = [
    'requirements', 'design', 'implementation', 'testing',
    'code_review', 'security_audit', 'documentation', 'deployment',
];

function formatTimeAgo(timestamp: string): string {
    const diff = Date.now() - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
}

function getStatusIcon(status: string): string {
    switch (status) {
        case 'running': return '▶️';
        case 'paused': return '⏸️';
        case 'awaiting_approval': return '🔔';
        case 'completed': return '✅';
        case 'failed': return '❌';
        case 'cancelled': return '⏹️';
        default: return '○';
    }
}

export default function WorkflowsPage() {
    const [workflows, setWorkflows] = useState<Workflow[]>(mockWorkflows);
    const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>(mockPendingApprovals);
    const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [useMock, setUseMock] = useState(true);

    // WebSocket for real-time updates
    const { connected, lastEvent } = useWorkflowWebSocket(selectedWorkflow, {
        onMessage: (event: WorkflowEvent) => {
            if (event.type === 'state_change') {
                setWorkflows(prev => prev.map(wf =>
                    wf.id === event.workflow_id
                        ? { ...wf, phase: event.data.phase || wf.phase, updated_at: event.data.timestamp }
                        : wf
                ));
            }
        },
    });

    // Fetch workflows
    const fetchWorkflows = useCallback(async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_BASE_URL}/workflows`);
            if (response.ok) {
                const data = await response.json();
                setWorkflows(data);
                setUseMock(false);
            }
        } catch (error) {
            console.warn('Using mock workflow data:', error);
            setUseMock(true);
        } finally {
            setLoading(false);
        }
    }, []);

    // Fetch pending approvals
    const fetchPendingApprovals = useCallback(async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/workflows/pending-approvals`);
            if (response.ok) {
                const data = await response.json();
                setPendingApprovals(data.approvals || []);
            }
        } catch (error) {
            console.warn('Using mock approval data');
        }
    }, []);

    // Handle approval
    const handleApproval = async (workflowId: string, approved: boolean, feedback?: string) => {
        try {
            const response = await fetch(`${API_BASE_URL}/workflows/${workflowId}/approval`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ approved, reviewer_id: 'user', feedback }),
            });

            if (response.ok) {
                // Remove from pending and refresh
                setPendingApprovals(prev => prev.filter(a => a.workflow_id !== workflowId));
                fetchWorkflows();
            }
        } catch (error) {
            console.error('Approval failed:', error);
        }
    };

    // Handle pause/resume
    const handlePauseResume = async (workflowId: string, action: 'pause' | 'resume') => {
        try {
            await fetch(`${API_BASE_URL}/workflows/${workflowId}/${action}`, { method: 'POST' });
            fetchWorkflows();
        } catch (error) {
            console.error(`${action} failed:`, error);
        }
    };

    useEffect(() => {
        fetchWorkflows();
        fetchPendingApprovals();
        const interval = setInterval(() => {
            fetchWorkflows();
            fetchPendingApprovals();
        }, 10000);
        return () => clearInterval(interval);
    }, [fetchWorkflows, fetchPendingApprovals]);

    const currentPhaseIndex = (phase: string) => phaseOrder.indexOf(phase);

    return (
        <div className="dashboard">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-logo">Aurora Dev</div>
                <nav className="sidebar-nav">
                    <a href="/" className="nav-item">
                        <span>📊</span> Dashboard
                    </a>
                    <div className="nav-item">
                        <span>🤖</span> Agents
                    </div>
                    <div className="nav-item">
                        <span>📝</span> Tasks
                    </div>
                    <div className="nav-item active">
                        <span>🔄</span> Workflows
                    </div>
                    <div className="nav-item">
                        <span>⚙️</span> Settings
                    </div>
                </nav>
                <div style={{ padding: "1rem", fontSize: "0.75rem" }}>
                    <div style={{ color: connected ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                        {connected ? '● Connected' : '○ Disconnected'}
                    </div>
                    {useMock && <div style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>⚠️ Mock data</div>}
                </div>
            </aside>

            {/* Main Content */}
            <main className="dashboard-main">
                <header className="header">
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Workflows</h1>
                    <div className="header-user">
                        <span>🔔</span>
                        <div className="user-avatar" />
                    </div>
                </header>

                {/* Pending Approvals Banner */}
                {pendingApprovals.length > 0 && (
                    <section className="approval-banner" style={{
                        background: 'linear-gradient(135deg, rgba(245,158,11,0.15), rgba(245,158,11,0.05))',
                        border: '1px solid rgba(245,158,11,0.3)',
                        borderRadius: '12px',
                        padding: '1.5rem',
                        marginBottom: '1.5rem',
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
                            <span style={{ fontSize: '1.5rem' }}>🔔</span>
                            <h2 style={{ fontSize: '1.125rem', fontWeight: 600 }}>
                                {pendingApprovals.length} Pending Approval{pendingApprovals.length > 1 ? 's' : ''}
                            </h2>
                        </div>

                        {pendingApprovals.map((approval) => (
                            <div key={approval.approval_id} style={{
                                background: 'var(--bg-main)',
                                borderRadius: '8px',
                                padding: '1rem',
                                marginBottom: '0.75rem',
                            }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div>
                                        <div style={{ fontWeight: 500 }}>{approval.context.description}</div>
                                        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                                            {approval.context.agent} • {approval.phase} phase • {formatTimeAgo(approval.requested_at)}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button
                                            onClick={() => handleApproval(approval.workflow_id, false)}
                                            style={{
                                                padding: '0.5rem 1rem',
                                                borderRadius: '6px',
                                                border: '1px solid var(--border)',
                                                background: 'transparent',
                                                cursor: 'pointer',
                                                color: 'var(--text-primary)',
                                            }}
                                        >
                                            Reject
                                        </button>
                                        <button
                                            onClick={() => handleApproval(approval.workflow_id, true)}
                                            style={{
                                                padding: '0.5rem 1rem',
                                                borderRadius: '6px',
                                                border: 'none',
                                                background: 'var(--accent-green)',
                                                color: 'white',
                                                cursor: 'pointer',
                                                fontWeight: 500,
                                            }}
                                        >
                                            Approve
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </section>
                )}

                {/* Workflows List */}
                <section className="workflows-list">
                    {workflows.map((workflow) => (
                        <div
                            key={workflow.id}
                            className="chart-card"
                            style={{
                                marginBottom: '1rem',
                                cursor: 'pointer',
                                border: selectedWorkflow === workflow.id ? '2px solid var(--accent-coral)' : undefined,
                            }}
                            onClick={() => setSelectedWorkflow(selectedWorkflow === workflow.id ? null : workflow.id)}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                    <span style={{ fontSize: '1.25rem' }}>{getStatusIcon(workflow.status)}</span>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{workflow.id}</div>
                                        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                                            {workflow.project_id} • {workflow.mode}
                                        </div>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                    <span style={{
                                        padding: '0.25rem 0.75rem',
                                        borderRadius: '9999px',
                                        fontSize: '0.75rem',
                                        fontWeight: 500,
                                        background: `${phaseColors[workflow.status] || phaseColors.idle}20`,
                                        color: phaseColors[workflow.status] || phaseColors.idle,
                                    }}>
                                        {workflow.status.replace('_', ' ')}
                                    </span>
                                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                        {formatTimeAgo(workflow.updated_at)}
                                    </span>
                                </div>
                            </div>

                            {/* Phase Progress Bar */}
                            <div style={{ display: 'flex', gap: '4px', marginBottom: '1rem' }}>
                                {phaseOrder.map((phase, index) => {
                                    const isActive = currentPhaseIndex(workflow.phase) >= index;
                                    const isCurrent = workflow.phase === phase;
                                    return (
                                        <div
                                            key={phase}
                                            style={{
                                                flex: 1,
                                                height: '8px',
                                                borderRadius: '4px',
                                                background: isActive
                                                    ? isCurrent
                                                        ? `linear-gradient(90deg, ${phaseColors[phase]}, ${phaseColors[phase]}80)`
                                                        : phaseColors[phase]
                                                    : 'var(--bg-elevated)',
                                                transition: 'all 0.3s ease',
                                            }}
                                            title={phase}
                                        />
                                    );
                                })}
                            </div>

                            {/* Expanded Details */}
                            {selectedWorkflow === workflow.id && (
                                <div style={{
                                    borderTop: '1px solid var(--border)',
                                    paddingTop: '1rem',
                                    marginTop: '0.5rem',
                                }}>
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
                                        <div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Current Phase</div>
                                            <div style={{ fontWeight: 500 }}>{workflow.phase}</div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Started</div>
                                            <div>{new Date(workflow.started_at).toLocaleString()}</div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Mode</div>
                                            <div style={{ textTransform: 'capitalize' }}>{workflow.mode}</div>
                                        </div>
                                    </div>

                                    {/* Action Buttons */}
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        {workflow.status === 'running' && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handlePauseResume(workflow.id, 'pause');
                                                }}
                                                style={{
                                                    padding: '0.5rem 1rem',
                                                    borderRadius: '6px',
                                                    border: '1px solid var(--border)',
                                                    background: 'transparent',
                                                    cursor: 'pointer',
                                                    color: 'var(--text-primary)',
                                                }}
                                            >
                                                ⏸️ Pause
                                            </button>
                                        )}
                                        {workflow.status === 'paused' && (
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handlePauseResume(workflow.id, 'resume');
                                                }}
                                                style={{
                                                    padding: '0.5rem 1rem',
                                                    borderRadius: '6px',
                                                    border: 'none',
                                                    background: 'var(--accent-green)',
                                                    color: 'white',
                                                    cursor: 'pointer',
                                                }}
                                            >
                                                ▶️ Resume
                                            </button>
                                        )}
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                window.open(`/workflows/${workflow.id}/graph`, '_blank');
                                            }}
                                            style={{
                                                padding: '0.5rem 1rem',
                                                borderRadius: '6px',
                                                border: '1px solid var(--border)',
                                                background: 'transparent',
                                                cursor: 'pointer',
                                                color: 'var(--text-primary)',
                                            }}
                                        >
                                            📊 View Graph
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </section>
            </main>
        </div>
    );
}
