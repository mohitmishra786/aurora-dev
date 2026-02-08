"""
Web interface package for AURORA-DEV dashboard.
"""
from aurora_dev.interfaces.web.dashboard import (
    DashboardDataProvider,
    DashboardStats,
    ChartData,
    router as dashboard_router,
)

__all__ = [
    "DashboardDataProvider",
    "DashboardStats",
    "ChartData",
    "dashboard_router",
]
