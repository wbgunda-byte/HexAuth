"""
API URLs for HexAUTH system.
"""
from django.urls import path, include
from . import views

app_name = 'api'

urlpatterns = [
    # Main API endpoint (matches KeyAuth structure)
    path('', views.MainAPIView.as_view(), name='main_api'),
    
    # Specific endpoints for better organization
    path('init/', views.InitializeView.as_view(), name='initialize'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('license/', views.LicenseLoginView.as_view(), name='license_login'),
    path('upgrade/', views.UpgradeView.as_view(), name='upgrade'),
    path('check/', views.CheckSessionView.as_view(), name='check_session'),
    path('log/', views.LogView.as_view(), name='log'),
    path('var/', views.VariableView.as_view(), name='variable'),
    path('setvar/', views.SetUserVariableView.as_view(), name='set_user_variable'),
    path('getvar/', views.GetUserVariableView.as_view(), name='get_user_variable'),
    path('file/', views.FileView.as_view(), name='file'),
    path('webhook/', views.WebhookView.as_view(), name='webhook'),
    path('ban/', views.BanView.as_view(), name='ban'),
    path('checkblacklist/', views.CheckBlacklistView.as_view(), name='check_blacklist'),
    path('chatget/', views.ChatGetView.as_view(), name='chat_get'),
    path('chatsend/', views.ChatSendView.as_view(), name='chat_send'),
    path('fetchonline/', views.FetchOnlineView.as_view(), name='fetch_online'),
    path('changeusername/', views.ChangeUsernameView.as_view(), name='change_username'),
    
    # Stats endpoint
    path('stats/', views.StatsView.as_view(), name='stats'),
]