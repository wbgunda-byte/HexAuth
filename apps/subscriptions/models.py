"""
Subscription models for HexAUTH system.
"""
from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel, TimestampedModel


class Subscription(BaseModel):
    """
    Subscription plans for applications.
    Replaces the 'subscriptions' table from KeyAuth.
    """
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=12)
    application = models.ForeignKey(
        'applications.Application', 
        on_delete=models.CASCADE, 
        related_name='subscriptions'
    )
    
    class Meta:
        db_table = 'subscriptions'
        unique_together = ['name', 'application']
        indexes = [
            models.Index(fields=['application', 'level']),
        ]
    
    def __str__(self):
        return f"{self.name} (Level {self.level})"


class UserSubscription(BaseModel):
    """
    User subscription instances.
    Replaces the 'subs' table from KeyAuth.
    """
    user = models.ForeignKey(
        'users.ApplicationUser', 
        on_delete=models.CASCADE, 
        related_name='subscriptions'
    )
    subscription = models.ForeignKey(
        Subscription, 
        on_delete=models.CASCADE,
        related_name='user_subscriptions'
    )
    application = models.ForeignKey(
        'applications.Application', 
        on_delete=models.CASCADE,
        related_name='user_subscriptions'
    )
    
    # Timing
    expires_at = models.DateTimeField()
    is_paused = models.BooleanField(default=False)
    paused_time_remaining = models.DurationField(null=True, blank=True)
    
    # License key that granted this subscription
    license_key = models.CharField(max_length=70, null=True, blank=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        indexes = [
            models.Index(fields=['user', 'application', 'expires_at']),
            models.Index(fields=['application', 'subscription', 'expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.subscription.name}"
    
    @property
    def is_active(self):
        """Check if subscription is currently active."""
        if self.is_paused:
            return False
        return self.expires_at > timezone.now()
    
    @property
    def time_remaining(self):
        """Get time remaining on subscription."""
        if self.is_paused and self.paused_time_remaining:
            return self.paused_time_remaining
        
        if self.expires_at <= timezone.now():
            return timezone.timedelta(0)
        
        return self.expires_at - timezone.now()
    
    def pause(self):
        """Pause the subscription."""
        if not self.is_paused and self.is_active:
            self.paused_time_remaining = self.time_remaining
            self.is_paused = True
            self.save(update_fields=['is_paused', 'paused_time_remaining'])
    
    def unpause(self):
        """Unpause the subscription."""
        if self.is_paused and self.paused_time_remaining:
            self.expires_at = timezone.now() + self.paused_time_remaining
            self.is_paused = False
            self.paused_time_remaining = None
            self.save(update_fields=['expires_at', 'is_paused', 'paused_time_remaining'])