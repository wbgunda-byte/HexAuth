"""
API serializers for HexAUTH system.
"""
from rest_framework import serializers
from apps.applications.models import Application
from apps.users.models import ApplicationUser
from apps.sessions.models import ApplicationSession
from apps.licenses.models import License
from apps.subscriptions.models import Subscription, UserSubscription


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Application model."""
    
    class Meta:
        model = Application
        fields = [
            'name', 'current_version', 'is_enabled', 'is_paused',
            'hwid_check_enabled', 'vpn_block_enabled'
        ]
        read_only_fields = fields


class ApplicationUserSerializer(serializers.ModelSerializer):
    """Serializer for ApplicationUser model."""
    
    class Meta:
        model = ApplicationUser
        fields = [
            'username', 'email', 'hwid', 'created_at', 
            'last_login', 'is_banned', 'ip_address'
        ]
        read_only_fields = ['created_at', 'last_login']


class SessionSerializer(serializers.ModelSerializer):
    """Serializer for ApplicationSession model."""
    
    class Meta:
        model = ApplicationSession
        fields = [
            'session_id', 'credential', 'is_validated', 
            'expires_at', 'ip_address'
        ]
        read_only_fields = fields


class LicenseSerializer(serializers.ModelSerializer):
    """Serializer for License model."""
    
    class Meta:
        model = License
        fields = [
            'key', 'level', 'status', 'expires_seconds',
            'generated_at', 'used_at', 'used_by', 'note'
        ]
        read_only_fields = fields


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""
    
    class Meta:
        model = Subscription
        fields = ['name', 'level']
        read_only_fields = fields


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for UserSubscription model."""
    subscription = SubscriptionSerializer(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'subscription', 'expires_at', 'is_paused', 
            'license_key', 'time_remaining'
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration."""
    username = serializers.CharField(max_length=70)
    password = serializers.CharField(max_length=128)
    email = serializers.EmailField(required=False, allow_blank=True)
    key = serializers.CharField(max_length=70)
    hwid = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    
    def validate_username(self, value):
        """Validate username length."""
        app = self.context.get('application')
        if app and len(value) < app.min_username_length:
            raise serializers.ValidationError("Username too short")
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    username = serializers.CharField(max_length=70)
    password = serializers.CharField(max_length=128)
    hwid = serializers.CharField(max_length=2000, required=False, allow_blank=True)
    token = serializers.CharField(max_length=32, required=False, allow_blank=True)