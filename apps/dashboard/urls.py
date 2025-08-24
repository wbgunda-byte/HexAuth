"""
Dashboard URLs for HexAUTH system.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.DashboardView.as_view(), name='home'),
    
    # Application management
    path('apps/', views.ApplicationListView.as_view(), name='applications'),
    path('apps/create/', views.ApplicationCreateView.as_view(), name='create_application'),
    path('apps/<uuid:pk>/', views.ApplicationDetailView.as_view(), name='application_detail'),
    path('apps/<uuid:pk>/settings/', views.ApplicationSettingsView.as_view(), name='application_settings'),
    
    # License management
    path('licenses/', views.LicenseListView.as_view(), name='licenses'),
    path('licenses/create/', views.LicenseCreateView.as_view(), name='create_license'),
    path('licenses/bulk-create/', views.LicenseBulkCreateView.as_view(), name='bulk_create_license'),
    
    # User management
    path('users/', views.ApplicationUserListView.as_view(), name='users'),
    path('users/<uuid:pk>/', views.ApplicationUserDetailView.as_view(), name='user_detail'),
    
    # Subscription management
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscriptions'),
    path('subscriptions/create/', views.SubscriptionCreateView.as_view(), name='create_subscription'),
    
    # Other features
    path('sessions/', views.SessionListView.as_view(), name='sessions'),
    path('files/', views.FileListView.as_view(), name='files'),
    path('variables/', views.VariableListView.as_view(), name='variables'),
    path('webhooks/', views.WebhookListView.as_view(), name='webhooks'),
    path('chat/', views.ChatView.as_view(), name='chat'),
    path('blacklists/', views.BlacklistView.as_view(), name='blacklists'),
    path('logs/', views.LogView.as_view(), name='logs'),
    path('audit-logs/', views.AuditLogView.as_view(), name='audit_logs'),
    
    # Account settings
    path('account/', views.AccountSettingsView.as_view(), name='account_settings'),
    path('account/logs/', views.AccountLogsView.as_view(), name='account_logs'),
]