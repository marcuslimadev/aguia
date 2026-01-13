"""
Páginas da interface gráfica
"""
from .login_page import LoginPage
from .dashboard_page import DashboardPage
from .cameras_page import CamerasPage, ZonesPage, AlertsPage, SettingsPage
from .live_view_page import LiveViewPage

__all__ = [
    'LoginPage',
    'DashboardPage',
    'CamerasPage',
    'ZonesPage',
    'AlertsPage',
    'SettingsPage',
    'LiveViewPage'
]
