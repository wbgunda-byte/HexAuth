"""
User account models for HexAUTH system.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel, TimestampedModel
import secrets


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    Replaces the 'accounts' table from KeyAuth.
    """
    
    class Role(models.TextChoices):
        TESTER = 'tester', 'Tester'
        DEVELOPER = 'developer', 'Developer'
        SELLER = 'seller', 'Seller'
        MANAGER = 'manager', 'Manager'
        RESELLER = 'reseller', 'Reseller'
        ADMIN = 'admin', 'Admin'
    
    # Core fields
    email = models.EmailField(unique=True)
    owner_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.TESTER)
    
    # Profile
    profile_image = models.URLField(
        max_length=200, 
        default='https://cdn.hexauth.com/assets/img/default-avatar.png'
    )
    
    # Subscription & billing
    subscription_expires = models.DateTimeField(null=True, blank=True)
    balance = models.JSONField(default=dict)  # Store balance for different durations
    key_levels = models.CharField(max_length=100, default='N/A')
    
    # Security
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)
    
    # Two-factor authentication
    two_factor_enabled = models.BooleanField(default=False)
    google_auth_secret = models.CharField(max_length=32, null=True, blank=True)
    
    # Security keys (WebAuthn)
    security_key_enabled = models.BooleanField(default=False)
    
    # Settings
    account_logs_enabled = models.BooleanField(default=True)
    email_verification_enabled = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=True)
    
    # Location tracking
    last_ip = models.GenericIPAddressField(null=True, blank=True)
    registration_ip = models.GenericIPAddressField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    as_number = models.CharField(max_length=20, null=True, blank=True)
    
    # Permissions for managers
    permissions = models.BigIntegerField(default=2047)  # All permissions by default
    
    # Relationships
    managed_application = models.ForeignKey(
        'applications.Application', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='managers'
    )
    owner = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='managed_users'
    )
    
    # Timestamps
    last_password_reset = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'accounts'
        indexes = [
            models.Index(fields=['email', 'username']),
            models.Index(fields=['owner_id']),
            models.Index(fields=['role']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.owner_id and self.role in [self.Role.DEVELOPER, self.Role.SELLER]:
            self.owner_id = self.generate_owner_id()
        super().save(*args, **kwargs)
    
    def generate_owner_id(self):
        """Generate a unique owner ID."""
        while True:
            owner_id = secrets.token_hex(5)  # 10 character hex string
            if not User.objects.filter(owner_id=owner_id).exists():
                return owner_id
    
    @property
    def is_subscription_active(self):
        """Check if user's subscription is active."""
        if not self.subscription_expires:
            return self.role == self.Role.TESTER
        return self.subscription_expires > timezone.now()
    
    @property
    def subscription_expires_soon(self):
        """Check if subscription expires within a month."""
        if not self.subscription_expires:
            return False
        return self.subscription_expires - timezone.now() < timedelta(days=30)


class AccountLog(TimestampedModel):
    """
    Account login/activity logs.
    Replaces the 'acclogs' table from KeyAuth.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    action = models.CharField(max_length=100, default='login')
    
    class Meta:
        db_table = 'account_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
        ordering = ['-created_at']


class SecurityKey(BaseModel):
    """
    WebAuthn security keys for users.
    Replaces the 'securityKeys' table from KeyAuth.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_keys')
    name = models.CharField(max_length=100)
    credential_id = models.TextField()
    credential_public_key = models.TextField()
    
    class Meta:
        db_table = 'security_keys'
        indexes = [
            models.Index(fields=['user']),
        ]


class EmailVerification(BaseModel):
    """
    Email verification tokens.
    Replaces the 'emailverify' table from KeyAuth.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    email = models.EmailField()
    new_email = models.EmailField(null=True, blank=True)
    new_username = models.CharField(max_length=150, null=True, blank=True)
    old_username = models.CharField(max_length=150, null=True, blank=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'email_verifications'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]


class PasswordReset(BaseModel):
    """
    Password reset tokens.
    Replaces the 'resets' table from KeyAuth.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'password_resets'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]