"""
Custom validators for HexAUTH system.
"""
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from .utils import check_password_breach


class LeakedPasswordValidator:
    """
    Validate that the password hasn't been leaked in data breaches.
    """
    
    def validate(self, password, user=None):
        if check_password_breach(password):
            raise ValidationError(
                _("This password has been leaked in a data breach. Please choose a different password."),
                code='password_leaked',
            )
    
    def get_help_text(self):
        return _("Your password must not have been leaked in any known data breaches.")


def validate_hwid_length(value):
    """
    Validate HWID meets minimum length requirements.
    """
    min_length = getattr(settings, 'HEXAUTH_SETTINGS', {}).get('MIN_HWID_LENGTH', 20)
    if value and len(value) < min_length:
        raise ValidationError(
            f'HWID must be at least {min_length} characters long.'
        )


def validate_license_key_format(value):
    """
    Validate license key format.
    """
    if not value:
        raise ValidationError('License key cannot be empty.')
    
    if len(value) > 70:
        raise ValidationError('License key must be 70 characters or less.')
    
    # Add more specific format validation if needed
    allowed_chars = set(string.ascii_letters + string.digits + '-')
    if not set(value).issubset(allowed_chars):
        raise ValidationError('License key contains invalid characters.')