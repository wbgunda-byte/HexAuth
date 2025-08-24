"""
API utility functions for HexAUTH system.
"""
import hashlib
import secrets
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from apps.core.utils import get_client_ip, check_password_breach


def encrypt_data(data, key, iv):
    """
    Encrypt data using AES-256-CBC (matching KeyAuth encryption).
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import binascii
    
    # Create key and IV from provided values
    key_hash = hashlib.sha256(key.encode()).digest()[:32]
    iv_hash = hashlib.sha256(iv.encode()).digest()[:16]
    
    # Pad data to 16-byte boundary
    padding_length = 16 - (len(data) % 16)
    padded_data = data + (chr(padding_length) * padding_length)
    
    # Encrypt
    cipher = Cipher(algorithms.AES(key_hash), modes.CBC(iv_hash), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data.encode()) + encryptor.finalize()
    
    return binascii.hexlify(encrypted).decode()


def decrypt_data(encrypted_data, key, iv):
    """
    Decrypt data using AES-256-CBC (matching KeyAuth decryption).
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import binascii
    
    try:
        # Create key and IV from provided values
        key_hash = hashlib.sha256(key.encode()).digest()[:32]
        iv_hash = hashlib.sha256(iv.encode()).digest()[:16]
        
        # Decrypt
        encrypted_bytes = binascii.unhexlify(encrypted_data)
        cipher = Cipher(algorithms.AES(key_hash), modes.CBC(iv_hash), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
        
        # Remove padding
        padding_length = decrypted[-1]
        return decrypted[:-padding_length].decode()
    except Exception:
        return None


def validate_session(session_id, application):
    """
    Validate and return session if valid.
    """
    try:
        session = ApplicationSession.objects.get(
            session_id=session_id,
            application=application,
            expires_at__gt=timezone.now()
        )
        return session
    except ApplicationSession.DoesNotExist:
        return None


def create_user_subscription(user, license_obj, application):
    """
    Create user subscription from license key.
    """
    # Find subscription for license level
    try:
        subscription = Subscription.objects.get(
            application=application,
            level=license_obj.level
        )
    except Subscription.DoesNotExist:
        return False, "No subscription found for license level"
    
    # Calculate expiry
    expires_at = timezone.now() + timezone.timedelta(seconds=license_obj.expires_seconds)
    
    # Create subscription
    UserSubscription.objects.create(
        user=user,
        subscription=subscription,
        application=application,
        expires_at=expires_at,
        license_key=license_obj.key
    )
    
    return True, subscription.name


def get_user_subscriptions(user, application):
    """
    Get active subscriptions for user.
    """
    subscriptions = UserSubscription.objects.filter(
        user=user,
        application=application,
        expires_at__gt=timezone.now(),
        is_paused=False
    ).select_related('subscription')
    
    result = []
    for sub in subscriptions:
        time_left = int((sub.expires_at - timezone.now()).total_seconds())
        result.append({
            'subscription': sub.subscription.name,
            'key': sub.license_key,
            'expiry': int(sub.expires_at.timestamp()),
            'timeleft': time_left,
            'level': sub.subscription.level
        })
    
    return result


def check_user_blacklist(user, application, ip_address):
    """
    Check if user/IP/HWID is blacklisted.
    """
    from apps.blacklists.models import Blacklist
    
    blacklists = Blacklist.objects.filter(
        application=application
    ).filter(
        models.Q(hwid=user.hwid) | models.Q(ip_address=ip_address)
    )
    
    return blacklists.exists()


def log_user_action(application, credential, message, pc_user=None):
    """
    Log user action to database or webhook.
    """
    from apps.audit.models import UserLog
    
    if len(message) > 275:
        return False
    
    # If webhook configured, send to Discord
    if application.webhook_url:
        from apps.core.utils import send_discord_webhook
        
        webhook_message = f"📜 Log: {message}"
        send_discord_webhook(application.webhook_url, webhook_message)
    else:
        # Store in database
        UserLog.objects.create(
            application=application,
            credential=credential,
            message=message,
            pc_user=pc_user
        )
    
    return True