"""
Application models for HexAUTH system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimestampedModel
import secrets

User = get_user_model()


class Application(BaseModel):
    """
    Application model representing a software project.
    Replaces the 'apps' table from KeyAuth.
    """
    
    # Basic info
    name = models.CharField(max_length=40)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_applications')
    secret = models.CharField(max_length=64, unique=True)
    
    # Status
    is_enabled = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    is_paused = models.BooleanField(default=False)
    
    # Security settings
    hwid_check_enabled = models.BooleanField(default=True)
    vpn_block_enabled = models.BooleanField(default=False)
    hash_check_enabled = models.BooleanField(default=False)
    force_hwid = models.BooleanField(default=True)
    min_hwid_length = models.IntegerField(default=20)
    
    # Version control
    current_version = models.CharField(max_length=10, default='1.0')
    download_url = models.URLField(max_length=200, null=True, blank=True)
    web_download_url = models.URLField(max_length=200, null=True, blank=True)
    file_hash = models.TextField(null=True, blank=True)
    
    # Webhooks
    webhook_url = models.URLField(max_length=200, null=True, blank=True)
    audit_log_webhook = models.URLField(max_length=200, null=True, blank=True)
    
    # Session settings
    session_expiry_seconds = models.IntegerField(default=21600)  # 6 hours
    kill_other_sessions = models.BooleanField(default=False)
    
    # User settings
    min_username_length = models.IntegerField(default=1)
    block_leaked_passwords = models.BooleanField(default=False)
    
    # Custom domain
    custom_domain = models.CharField(max_length=253, null=True, blank=True)
    custom_domain_api = models.CharField(max_length=253, null=True, blank=True)
    
    # Panel settings
    panel_enabled = models.BooleanField(default=True)
    customer_panel_icon = models.URLField(
        max_length=200, 
        default='https://cdn.hexauth.com/assets/img/favicon.png'
    )
    
    # Reseller settings
    reseller_store_url = models.URLField(max_length=100, null=True, blank=True)
    seller_key = models.CharField(max_length=32, null=True, blank=True)
    seller_logs_enabled = models.BooleanField(default=False)
    seller_api_whitelist = models.CharField(max_length=50, null=True, blank=True)
    
    # Token system
    token_system_enabled = models.BooleanField(default=False)
    
    # License generation settings
    license_format = models.CharField(
        max_length=100, 
        default='******-******-******-******-******-******'
    )
    license_amount = models.IntegerField(null=True, blank=True)
    license_level = models.IntegerField(null=True, blank=True)
    license_note = models.CharField(max_length=100, null=True, blank=True)
    license_duration = models.IntegerField(null=True, blank=True)
    license_unit = models.IntegerField(null=True, blank=True)
    
    # Cooldown settings
    cooldown_seconds = models.IntegerField(default=604800)  # 1 week
    cooldown_unit = models.IntegerField(default=86400)  # 1 day
    
    class Meta:
        db_table = 'applications'
        unique_together = ['name', 'owner']
        indexes = [
            models.Index(fields=['secret']),
            models.Index(fields=['owner', 'name']),
            models.Index(fields=['custom_domain']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.secret:
            self.secret = self.generate_secret()
        if not self.seller_key:
            self.seller_key = secrets.token_hex(16)
        super().save(*args, **kwargs)
    
    def generate_secret(self):
        """Generate a unique application secret."""
        while True:
            secret = secrets.token_hex(32)
            if not Application.objects.filter(secret=secret).exists():
                return secret
    
    @property
    def customer_panel_url(self):
        """Get customer panel URL."""
        return f"https://hexauth.com/panel/{self.owner.username}/{self.name}/"


class ApplicationSettings(BaseModel):
    """
    Custom error messages and settings for applications.
    """
    application = models.OneToOneField(
        Application, 
        on_delete=models.CASCADE, 
        related_name='settings'
    )
    
    # Custom error messages
    app_disabled_msg = models.CharField(
        max_length=100, 
        default='This application is disabled'
    )
    username_taken_msg = models.CharField(
        max_length=100, 
        default='Username already taken, choose a different one'
    )
    key_not_found_msg = models.CharField(
        max_length=100, 
        default='Invalid license key'
    )
    key_used_msg = models.CharField(
        max_length=100, 
        default='License key has already been used'
    )
    no_sub_level_msg = models.CharField(
        max_length=100, 
        default='There is no subscription created for your key level. Contact application developer.'
    )
    username_not_found_msg = models.CharField(
        max_length=100, 
        default='Invalid username'
    )
    password_mismatch_msg = models.CharField(
        max_length=100, 
        default='Password does not match.'
    )
    hwid_mismatch_msg = models.CharField(
        max_length=100, 
        default="HWID doesn't match. Ask for a HWID reset"
    )
    no_active_subs_msg = models.CharField(
        max_length=100, 
        default='No active subscription(s) found'
    )
    hwid_blacklisted_msg = models.CharField(
        max_length=100, 
        default="You've been blacklisted from our application"
    )
    paused_sub_msg = models.CharField(
        max_length=100, 
        default="Your subscription is paused and can't be used right now"
    )
    vpn_blocked_msg = models.CharField(
        max_length=100, 
        default='VPNs are blocked on this application'
    )
    key_banned_msg = models.CharField(
        max_length=100, 
        default='Your license is banned'
    )
    user_banned_msg = models.CharField(
        max_length=100, 
        default='The user is banned'
    )
    session_unauthed_msg = models.CharField(
        max_length=100, 
        default='Session is not validated'
    )
    hash_check_fail_msg = models.CharField(
        max_length=100, 
        default="This program hash does not match, make sure you're using latest version"
    )
    logged_in_msg = models.CharField(
        max_length=100, 
        default='Logged in!'
    )
    paused_app_msg = models.CharField(
        max_length=100, 
        default='Application is currently paused, please wait for the developer to say otherwise.'
    )
    username_too_short_msg = models.CharField(
        max_length=100, 
        default='Username too short, try longer one.'
    )
    password_leaked_msg = models.CharField(
        max_length=100, 
        default='This password has been leaked in a data breach (not from us), please use a different one.'
    )
    chat_hit_delay_msg = models.CharField(
        max_length=100, 
        default="Chat slower, you've hit the delay limit"
    )
    token_invalid_msg = models.CharField(
        max_length=100, 
        default='Token Invalid'
    )
    
    class Meta:
        db_table = 'application_settings'