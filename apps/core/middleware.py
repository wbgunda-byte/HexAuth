"""
Custom middleware for HexAUTH system.
"""
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from .utils import get_client_ip, rate_limit_key

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Custom security middleware for additional protection.
    """
    
    def process_request(self, request):
        """
        Process incoming requests for security checks.
        """
        # Log suspicious requests
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if any(bot in user_agent.lower() for bot in ['bot', 'crawler', 'spider']):
            logger.info(f"Bot request from {get_client_ip(request)}: {user_agent}")
        
        # Rate limiting for API endpoints
        if request.path.startswith('/api/'):
            ip = get_client_ip(request)
            rate_key = rate_limit_key(request, 'api', lambda r: ip)
            
            current_requests = cache.get(rate_key, 0)
            if current_requests >= 100:  # 100 requests per hour
                return JsonResponse({
                    'success': False,
                    'message': 'Rate limit exceeded. Please try again later.'
                }, status=429)
            
            cache.set(rate_key, current_requests + 1, 3600)  # 1 hour
        
        return None
    
    def process_response(self, request, response):
        """
        Process outgoing responses.
        """
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to log user actions for audit purposes.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Log user actions for audit trail.
        """
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'DELETE']:
            from apps.audit.models import AuditLog
            
            # Skip logging for certain endpoints
            skip_paths = ['/api/v1/log/', '/api/v1/check/']
            if not any(request.path.startswith(path) for path in skip_paths):
                try:
                    AuditLog.objects.create(
                        user=request.user,
                        action=f"{request.method} {request.path}",
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:400],
                        application=getattr(request.user, 'current_application', None)
                    )
                except Exception as e:
                    logger.error(f"Failed to create audit log: {e}")
        
        return None