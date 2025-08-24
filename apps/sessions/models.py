"""
Session models for HexAUTH system.
"""
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel
import secrets


class ApplicationSession(BaseModel):
    """
    Application user sessions.
    Replaces the 'sessions' table from KeyAuth.
    """
    session_id = models.CharField(max_length=32, unique=True)
    application = models.ForeignKey(
        'applications.Application', 
        on_delete=models.CASCADE, 
        related_name='sessions'
    )
    
    # User info
    credential = models.CharField(max_length=70, null=True, blank=True)
    is_validated = models.BooleanField(default=False)
    
    # Session data
    encryption_key = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'application_sessions'
        indexes = [
            models.Index(fields=['session_id', 'application']),
            models.Index(fields=['application', 'is_validated', 'expires_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.session_id:
            self.session_id = self.generate_session_id()
        super().save(*args, **kwargs)
    
    def generate_session_id(self):
        """Generate a unique session ID."""
        while True:
            session_id = secrets.token_hex(16)
            if not ApplicationSession.objects.filter(session_id=session_id).exists():
                return session_id
    
    @property
    def is_expired(self):
        """Check if session has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_active(self):
        """Check if session is active and valid."""
        return self.is_validated and not self.is_expired