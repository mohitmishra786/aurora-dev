/**
 * API client for Aurora Dev Dashboard
 * 
 * Connects to the FastAPI backend to fetch dashboard data
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface DashboardStats {
    total_projects: number;
    active_projects: number;
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    pending_tasks: number;
    running_tasks: number;
    total_agents: number;
    active_agents: number;
    total_tokens_used: number;
    total_cost_usd: number;
    daily_cost_usd: number;
    period_start: string;
    period_end: string;
}

export interface TimelineDataPoint {
    timestamp: string;
    value: number;
    label?: string;
}

export interface ChartData {
    chart_type: string;
    title: string;
    data: Record<string, any>[];
    x_label?: string;
    y_label?: string;
    legend?: string[];
}

export interface AgentInfo {
    id: string;
    name: string;
    role: string;
    status: 'active' | 'idle' | 'working' | 'error';
    tasks_completed: number;
    tokens_used: number;
}

export interface ActivityEvent {
    id: string;
    timestamp: string;
    agent: string;
    action: string;
    target: string;
    status: 'success' | 'pending' | 'error';
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
        const url = `${this.baseUrl}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options?.headers,
                },
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status} ${response.statusText}`);
            }

            return response.json();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // Dashboard endpoints
    async getStats(projectId?: string, periodDays: number = 7): Promise<DashboardStats> {
        const params = new URLSearchParams();
        if (projectId) params.append('project_id', projectId);
        params.append('period_days', periodDays.toString());

        return this.fetch(`/dashboard/stats?${params}`);
    }

    async getTaskTimeline(projectId?: string, days: number = 7): Promise<ChartData> {
        const params = new URLSearchParams();
        if (projectId) params.append('project_id', projectId);
        params.append('days', days.toString());

        return this.fetch(`/dashboard/charts/task-timeline?${params}`);
    }

    async getAgentWorkload(): Promise<ChartData> {
        return this.fetch('/dashboard/charts/agent-workload');
    }

    async getCostBreakdown(projectId?: string, days: number = 30): Promise<ChartData> {
        const params = new URLSearchParams();
        if (projectId) params.append('project_id', projectId);
        params.append('days', days.toString());

        return this.fetch(`/dashboard/charts/cost-breakdown?${params}`);
    }

    async getAgentNetwork(): Promise<ChartData> {
        return this.fetch('/dashboard/charts/agent-network');
    }

    // Agent endpoints
    async getAgents(): Promise<AgentInfo[]> {
        return this.fetch('/agents');
    }

    async getAgent(agentId: string): Promise<AgentInfo> {
        return this.fetch(`/agents/${agentId}`);
    }

    // Activity endpoints  
    async getRecentActivity(limit: number = 10): Promise<ActivityEvent[]> {
        return this.fetch(`/activity/recent?limit=${limit}`);
    }
}

// Singleton instance
export const api = new ApiClient();

// Mock data for development (when API is not available)
export const mockStats: DashboardStats = {
    total_projects: 12,
    active_projects: 5,
    total_tasks: 156,
    completed_tasks: 142,
    failed_tasks: 4,
    pending_tasks: 8,
    running_tasks: 2,
    total_agents: 8,
    active_agents: 5,
    total_tokens_used: 2847000,
    total_cost_usd: 45.32,
    daily_cost_usd: 6.47,
    period_start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    period_end: new Date().toISOString(),
};

export const mockAgents: AgentInfo[] = [
    { id: '1', name: 'Maestro', role: 'Orchestrator', status: 'active', tasks_completed: 156, tokens_used: 450000 },
    { id: '2', name: 'Architect', role: 'Design', status: 'idle', tasks_completed: 42, tokens_used: 280000 },
    { id: '3', name: 'Backend Dev', role: 'Backend', status: 'working', tasks_completed: 89, tokens_used: 520000 },
    { id: '4', name: 'Frontend Dev', role: 'Frontend', status: 'active', tasks_completed: 67, tokens_used: 380000 },
    { id: '5', name: 'Security', role: 'Security', status: 'idle', tasks_completed: 23, tokens_used: 120000 },
];

export const mockActivity: ActivityEvent[] = [
    { id: '1', timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(), agent: 'Backend Dev', action: 'Committed code', target: 'api/routes.py', status: 'success' },
    { id: '2', timestamp: new Date(Date.now() - 12 * 60 * 1000).toISOString(), agent: 'Architect', action: 'Updated design', target: 'system architecture', status: 'success' },
    { id: '3', timestamp: new Date(Date.now() - 25 * 60 * 1000).toISOString(), agent: 'Security', action: 'Security scan', target: 'dependencies', status: 'pending' },
    { id: '4', timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(), agent: 'Frontend Dev', action: 'UI component', target: 'Dashboard.tsx', status: 'success' },
    { id: '5', timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(), agent: 'Maestro', action: 'Task assigned', target: 'Sprint #12', status: 'success' },
];

// Fetch with fallback to mock data
export async function fetchDashboardData() {
    try {
        const stats = await api.getStats();
        return { stats, useMock: false };
    } catch {
        console.warn('API unavailable, using mock data');
        return { stats: mockStats, useMock: true };
    }
}
