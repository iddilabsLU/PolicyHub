"""
PolicyHub Views Package

Contains all application view components.
"""

from ui.views.base_view import BaseView, CenteredView, ScrollableView
from ui.views.login_view import LoginView
from ui.views.admin_creation_view import AdminCreationView
from ui.views.setup_view import SetupView
from ui.views.force_password_view import ForcePasswordChangeView
from ui.views.iddilabs_view import IddiLabsView
from ui.views.dashboard_view import DashboardView
from ui.views.register_view import RegisterView
from ui.views.reports_view import ReportsView
from ui.views.settings_view import SettingsView
from ui.views.document_detail_view import DocumentDetailView
from ui.views.main_view import MainView

__all__ = [
    "BaseView",
    "CenteredView",
    "ScrollableView",
    "LoginView",
    "AdminCreationView",
    "SetupView",
    "ForcePasswordChangeView",
    "IddiLabsView",
    "DashboardView",
    "RegisterView",
    "ReportsView",
    "SettingsView",
    "DocumentDetailView",
    "MainView",
]
