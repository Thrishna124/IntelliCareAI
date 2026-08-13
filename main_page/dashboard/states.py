"""
Dashboard States

Defines the possible states of the dashboard.
"""

from enum import Enum


class DashboardState(Enum):
    NO_PATIENT = "NO_PATIENT"
    READY = "READY"