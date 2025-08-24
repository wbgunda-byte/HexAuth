"""
Application user models for HexAUTH system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.core.models import BaseModel, TimestampedModel
from apps.core.validators import validate_hwid_length

User = get_user_model()


class ApplicationUser(BaseModel):
    """
    Users of client applications (not dashboard users).
    Replaces the 'users' table from KeyAuth.
    """
    username = models.CharField(max_length=70)
    email = models.EmailField(null=True, blank=True)
    password = models.CharField(max_length=60, null=True, blank=True)  # bcrypt hash
    hwid = models.TextField(null=True, blank=True, validators=[validate_hwid_length])
    
    # Application relationship
    application = models.ForeignKey(
        'applications.Application', 
        on_delete=models.CASCADE, 
        related_name='app_users'
    )
    
    # Owner (for reseller system)
    owner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_app_users'
    )
    
    # Timestamps
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Security
    is_banned = models.BooleanField(default=False)
    ban_reason = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    cooldown_until = models.DateTimeField(null=True, blank=True)
    
    # 2FA for app users
    two_factor_enabled = models.BooleanField(default=False)
    google_auth_secret = models.CharField(max_length=32, null=True, blank=True)
    
    class Meta:
        db_table = 'application_users'
        unique_together = ['username', 'application']
        indexes = [
            models.Index(fields=['application', 'username']),
            models.Index(fields=['application', 'hwid']),
            models.Index(fields=['owner']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.application.name})"
    
    @property
    def is_on_cooldown(self):
        """Check if user is on cooldown."""
        if not self.cooldown_until:
            return False
        return timezone.now() < self.cooldown_until
    
    def ban(self, reason="User banned"):
        """Ban this user."""
        self.is_banned = True
        self.ban_reason = reason
        self.save(update_fields=['is_banned', 'ban_reason'])
    
    def unban(self):
        """Unban this user."""
        self.is_banned = False
        self.ban_reason = None
        self.save(update_fields=['is_banned', 'ban_reason'])


class UserVariable(BaseModel):
    """
    User-specific variables.
    Replaces the 'uservars' table from KeyAuth.
    """
    name = models.CharField(max_length=100)
    data = models.CharField(max_length=500)
    user = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE, related_name='variables')
    application = models.ForeignKey(
        'applications.Application', 
        on_delete=models.CASCADE,
        related_name='user_variables'
    )
    is_read_only = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_variables'
        unique_together = ['name', 'user', 'application']
        indexes = [
            models.Index(fields=['application', 'name', 'user']),
        ]
    
    def __str__(self):
        return f"{self.name} = {self.data[:50]}..."


class UserPasswordReset(BaseModel):
    """
    Password reset tokens for application users.
    Replaces the 'resetUsers' table from KeyAuth.
    """
    user = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_password_resets'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]