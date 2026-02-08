"use client";

import { useState, useEffect, useCallback } from "react";
import {
  api,
  mockStats,
  mockAgents,
  mockActivity,
  type DashboardStats,
  type AgentInfo,
  type ActivityEvent
} from "@/lib/api";

// Custom hook for dashboard data
function useDashboardData() {
  const [stats, setStats] = useState<DashboardStats>(mockStats);
  const [agents, setAgents] = useState<AgentInfo[]>(mockAgents);
  const [activity, setActivity] = useState<ActivityEvent[]>(mockActivity);
  const [loading, setLoading] = useState(true);
  const [useMock, setUseMock] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [statsData, agentsData, activityData] = await Promise.allSettled([
        api.getStats(),
        api.getAgents(),
        api.getRecentActivity(5),
      ]);

      if (statsData.status === 'fulfilled') {
        setStats(statsData.value);
        setUseMock(false);
      }
      if (agentsData.status === 'fulfilled') {
        setAgents(agentsData.value);
      }
      if (activityData.status === 'fulfilled') {
        setActivity(activityData.value);
      }
    } catch (error) {
      console.warn('Using mock data:', error);
      setUseMock(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { stats, agents, activity, loading, useMock, refetch: fetchData };
}

// Format numbers for display
function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
  return num.toString();
}

// Format relative time
function formatTimeAgo(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const { stats, agents, activity, loading, useMock } = useDashboardData();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // Calculate success rate
  const successRate = stats.completed_tasks > 0
    ? ((stats.completed_tasks - stats.failed_tasks) / stats.completed_tasks * 100).toFixed(1)
    : "0.0";

  // Stat cards data derived from API
  const statCards = [
    { label: "Total Tasks", value: formatNumber(stats.total_tasks), change: "+12%", trend: "up" as const },
    { label: "Active Agents", value: stats.active_agents.toString(), change: `+${stats.active_agents - 3}`, trend: "up" as const },
    { label: "Success Rate", value: `${successRate}%`, change: "+3.1%", trend: "up" as const },
    { label: "Token Usage", value: formatNumber(stats.total_tokens_used), change: "-5%", trend: "down" as const },
  ];

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">Aurora Dev</div>
        <nav className="sidebar-nav">
          <div className="nav-item active">
            <span>📊</span> Dashboard
          </div>
          <div className="nav-item">
            <span>🤖</span> Agents
          </div>
          <div className="nav-item">
            <span>📝</span> Tasks
          </div>
          <div className="nav-item">
            <span>🔄</span> Workflows
          </div>
          <div className="nav-item">
            <span>⚙️</span> Settings
          </div>
        </nav>
        {useMock && (
          <div style={{ padding: "1rem", fontSize: "0.75rem", color: "var(--text-muted)", opacity: 0.6 }}>
            ⚠️ Using mock data
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        {/* Header */}
        <header className="header">
          <input
            type="text"
            className="header-search"
            placeholder="Search tasks, agents, or projects..."
          />
          <div className="header-user">
            <span>🔔</span>
            <div className="user-avatar" />
          </div>
        </header>

        {/* Stats Grid */}
        <section className="stats-grid">
          {statCards.map((stat, index) => (
            <div key={index} className="card animate-fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
              <div className="card-title">{stat.label}</div>
              <div className="card-value">{loading ? "..." : stat.value}</div>
              <div className="card-subtext" style={{ color: stat.trend === "up" ? "var(--accent-green)" : "var(--accent-coral)" }}>
                {stat.change} from last week
              </div>
            </div>
          ))}
        </section>

        {/* Main Grid */}
        <div className="dashboard-grid">
          {/* Chart Card */}
          <div className="chart-card">
            <div className="chart-header">
              <h2 className="chart-title">Task Activity</h2>
              <div className="chart-period">
                <button className="period-btn">7D</button>
                <button className="period-btn active">1M</button>
                <button className="period-btn">1Y</button>
              </div>
            </div>
            <div style={{ height: 200, display: "flex", alignItems: "flex-end", gap: 8, padding: "20px 0" }}>
              {[65, 45, 85, 70, 90, 60, 95, 80, 75, 88, 92, 78].map((height, i) => (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    height: `${height}%`,
                    background: `linear-gradient(to top, var(--accent-coral), var(--accent-coral-light))`,
                    borderRadius: 6,
                    opacity: 0.8 + i * 0.02,
                  }}
                />
              ))}
            </div>
          </div>

          {/* Agents Card */}
          <div className="chart-card">
            <div className="chart-header">
              <h2 className="chart-title">Top Agents</h2>
              <button className="period-btn">See All →</button>
            </div>
            <div className="agent-list">
              {agents.slice(0, 4).map((agent) => (
                <div key={agent.id} className="agent-item">
                  <div className={`agent-avatar ${agent.role.toLowerCase().replace(' ', '-')}`}>
                    {agent.name[0]}
                  </div>
                  <div className="agent-info">
                    <div className="agent-name">{agent.name}</div>
                    <div className="agent-role">{agent.role}</div>
                  </div>
                  <span className={`agent-status ${agent.status}`}>
                    {agent.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Activity Timeline */}
        <div className="chart-card">
          <div className="chart-header">
            <h2 className="chart-title">Recent Activity</h2>
          </div>
          <div className="timeline">
            {activity.map((item, index) => (
              <div key={item.id || index} className="timeline-item">
                <span className="timeline-time">{formatTimeAgo(item.timestamp)}</span>
                <span className="timeline-content">
                  <span className="timeline-highlight">{item.agent}</span> {item.action}
                  {item.target && <span style={{ opacity: 0.7 }}> • {item.target}</span>}
                </span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

