"""
License key models for HexAUTH system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimestampedModel
from apps.core.validators import validate_license_key_format

User = get_user_model()


class License(BaseModel):
    """
    License key model.
    Replaces the 'keys' table from KeyAuth.
    """
    
    class Status(models.TextChoices):
        NOT_USED = 'not_used', 'Not Used'
        USED = 'used', 'Used'
        BANNED = 'banned', 'Banned'
    
    # Core fields
    key = models.CharField(
        max_length=70, 
        validators=[validate_license_key_format],
        db_index=True
    )
    application = models.ForeignKey(
        'applications.Application', 
        on_delete=models.CASCADE, 
        related_name='licenses'
    )
    
    # Metadata
    note = models.CharField(max_length=100, null=True, blank=True)
    level = models.CharField(max_length=12, default='1')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_USED)
    
    # Expiry
    expires_seconds = models.BigIntegerField()  # Duration in seconds
    
    # Generation info
    generated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='generated_licenses'
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    
    # Usage info
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.CharField(max_length=70, null=True, blank=True)
    
    # Ban info
    ban_reason = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        db_table = 'licenses'
        unique_together = ['key', 'application']
        indexes = [
            models.Index(fields=['application', 'key']),
            models.Index(fields=['application', 'status']),
            models.Index(fields=['generated_by']),
        ]
    
    def __str__(self):
        return f"{self.key} ({self.application.name})"
    
    @property
    def is_expired(self):
        """Check if license has expired based on usage."""
        if self.status != self.Status.USED or not self.used_at:
            return False
        
        from django.utils import timezone
        expiry_time = self.used_at + timezone.timedelta(seconds=self.expires_seconds)
        return timezone.now() > expiry_time
    
    def ban(self, reason="License banned"):
        """Ban this license key."""
        self.status = self.Status.BANNED
        self.ban_reason = reason
        self.save(update_fields=['status', 'ban_reason'])
    
    def unban(self):
        """Unban this license key."""
        original_status = self.Status.USED if self.used_by else self.Status.NOT_USED
        self.status = original_status
        self.ban_reason = None
        self.save(update_fields=['status', 'ban_reason'])