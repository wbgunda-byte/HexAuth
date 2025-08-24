"""
API views for HexAUTH system.
Replicates KeyAuth API functionality with Django REST Framework.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
import hashlib
import secrets
import logging

from apps.applications.models import Application
from apps.users.models import ApplicationUser
from apps.sessions.models import ApplicationSession
from apps.licenses.models import License
from apps.subscriptions.models import Subscription, UserSubscription
from apps.blacklists.models import Blacklist
from apps.variables.models import Variable
from apps.files.models import File
from apps.webhooks.models import Webhook
from apps.chat.models import ChatChannel, ChatMessage
from apps.audit.models import AuditLog

from .serializers import *
from .utils import *
from apps.core.utils import get_client_ip, check_vpn_proxy, generate_random_string

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """
    Base API view with common functionality.
    """
    permission_classes = [AllowAny]
    
    def get_application(self, owner_id, name):
        """Get application by owner_id and name."""
        try:
            return Application.objects.select_related('owner').get(
                owner__owner_id=owner_id,
                name=name
            )
        except Application.DoesNotExist:
            return None
    
    def validate_application(self, request):
        """Validate application credentials."""
        owner_id = request.data.get('ownerid') or request.GET.get('ownerid')
        name = request.data.get('name') or request.GET.get('name')
        
        if not owner_id:
            return None, self.error_response("No OwnerID specified. Select app & copy code snippet from HexAUTH dashboard.")
        
        if not name:
            return None, self.error_response("No app name specified. Select app & copy code snippet from HexAUTH dashboard.")
        
        if len(owner_id) != 10:
            return None, self.error_response("OwnerID should be 10 characters long.")
        
        app = self.get_application(owner_id, name)
        if not app:
            return None, Response("HexAUTH_Invalid", status=status.HTTP_400_BAD_REQUEST)
        
        if app.is_banned:
            return None, self.error_response("This application has been banned from HexAUTH for violating terms.")
        
        return app, None
    
    def error_response(self, message):
        """Return standardized error response."""
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def success_response(self, message, data=None):
        """Return standardized success response."""
        response_data = {
            'success': True,
            'message': message
        }
        if data:
            response_data.update(data)
        return Response(response_data)


class MainAPIView(BaseAPIView):
    """
    Main API endpoint that routes to specific handlers based on 'type' parameter.
    Maintains compatibility with KeyAuth API structure.
    """
    
    def post(self, request):
        """Handle POST requests with type-based routing."""
        request_type = request.data.get('type')
        
        if not request_type:
            return self.error_response("No type specified")
        
        # Route to appropriate handler
        handlers = {
            'init': self.handle_init,
            'register': self.handle_register,
            'login': self.handle_login,
            'license': self.handle_license,
            'upgrade': self.handle_upgrade,
            'check': self.handle_check,
            'log': self.handle_log,
            'var': self.handle_var,
            'setvar': self.handle_setvar,
            'getvar': self.handle_getvar,
            'file': self.handle_file,
            'webhook': self.handle_webhook,
            'ban': self.handle_ban,
            'checkblacklist': self.handle_checkblacklist,
            'chatget': self.handle_chatget,
            'chatsend': self.handle_chatsend,
            'fetchOnline': self.handle_fetchonline,
            'changeUsername': self.handle_changeusername,
        }
        
        handler = handlers.get(request_type)
        if not handler:
            return self.error_response("Unhandled Type")
        
        return handler(request)
    
    def handle_init(self, request):
        """Initialize application session."""
        app, error_response = self.validate_application(request)
        if error_response:
            return error_response
        
        # Check application status
        if not app.is_enabled:
            return self.error_response(app.settings.app_disabled_msg)
        
        if app.is_paused:
            return self.error_response(app.settings.paused_app_msg)
        
        # Version check
        version = request.data.get('ver') or request.GET.get('ver')
        if version and version != app.current_version:
            return Response({
                'success': False,
                'message': 'invalidver',
                'download': app.download_url
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Hash check
        if app.hash_check_enabled:
            client_hash = request.data.get('hash') or request.GET.get('hash')
            if client_hash and app.file_hash:
                if client_hash not in app.file_hash:
                    return self.error_response(app.settings.hash_check_fail_msg)
        
        # VPN/Proxy check
        ip = get_client_ip(request)
        if app.vpn_block_enabled and check_vpn_proxy(ip):
            # Check whitelist
            from apps.blacklists.models import Whitelist
            if not Whitelist.objects.filter(application=app, ip_address=ip).exists():
                return self.error_response(app.settings.vpn_blocked_msg)
        
        # Create or get session
        session = ApplicationSession.objects.create(
            application=app,
            ip_address=ip,
            expires_at=timezone.now() + timezone.timedelta(seconds=app.session_expiry_seconds)
        )
        
        # Get app stats (simplified for now)
        return self.success_response("Initialized", {
            'sessionid': session.session_id,
            'appinfo': {
                'numUsers': 'N/A - Use fetchStats() function',
                'numOnlineUsers': 'N/A - Use fetchStats() function', 
                'numKeys': 'N/A - Use fetchStats() function',
                'version': app.current_version,
                'customerPanelLink': app.customer_panel_url
            }
        })
    
    def handle_register(self, request):
        """Handle user registration."""
        # Implementation for user registration
        # This would be quite extensive, so showing structure
        pass
    
    def handle_login(self, request):
        """Handle user login."""
        # Implementation for user login
        pass
    
    # ... other handlers would follow similar pattern


class InitializeView(BaseAPIView):
    """
    Dedicated view for application initialization.
    """
    
    def post(self, request):
        """Initialize application session."""
        app, error_response = self.validate_application(request)
        if error_response:
            return error_response
        
        # Detailed implementation here
        return self.success_response("Initialized")


class StatsView(APIView):
    """
    Public statistics endpoint.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get public statistics."""
        # Cache stats for 1 hour
        stats = cache.get('hexauth_public_stats')
        
        if not stats:
            from django.db.models import Count
            
            stats = {
                'accounts': User.objects.count(),
                'applications': Application.objects.count(),
                'licenses': License.objects.count(),
                'activeUsers': ApplicationSession.objects.filter(
                    is_validated=True,
                    expires_at__gt=timezone.now()
                ).values('ip_address', 'application').distinct().count()
            }
            
            cache.set('hexauth_public_stats', stats, 3600)  # 1 hour
        
        return Response(stats)