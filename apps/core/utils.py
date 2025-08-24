"""
Core utilities for HexAUTH system.
"""
import hashlib
import secrets
import string
import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def generate_random_string(length=10, include_uppercase=True, include_lowercase=True, include_numbers=True):
    """
    Generate a random string with specified character sets.
    """
    characters = ''
    if include_lowercase:
        characters += string.ascii_lowercase
    if include_uppercase:
        characters += string.ascii_uppercase
    if include_numbers:
        characters += string.digits
    
    if not characters:
        characters = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_license_key(mask='******-******-******-******-******-******'):
    """
    Generate a license key based on a mask pattern.
    * = random character
    - = literal dash
    """
    result = ''
    for char in mask:
        if char == '*':
            result += secrets.choice(string.ascii_uppercase + string.digits)
        else:
            result += char
    return result


def get_client_ip(request):
    """
    Get the real client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Check for Cloudflare
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip:
        ip = cf_connecting_ip
    
    return ip


def check_vpn_proxy(ip_address):
    """
    Check if an IP address is a VPN or proxy using ip-api.com.
    """
    try:
        cache_key = f'vpn_check_{ip_address}'
        result = cache.get(cache_key)
        
        if result is not None:
            return result
        
        url = f"http://ip-api.com/json/{ip_address}?fields=16908288"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            is_vpn = data.get('proxy', False) or data.get('hosting', False)
            
            # Cache result for 1 hour
            cache.set(cache_key, is_vpn, 3600)
            return is_vpn
        
        return False
    except Exception as e:
        logger.error(f"VPN check failed for IP {ip_address}: {e}")
        return False


def check_password_breach(password):
    """
    Check if password has been breached using HaveIBeenPwned API.
    """
    try:
        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]
        
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            hashes = response.text.splitlines()
            for hash_line in hashes:
                hash_suffix, count = hash_line.split(':')
                if hash_suffix == suffix:
                    return True
        
        return False
    except Exception as e:
        logger.error(f"Password breach check failed: {e}")
        return False


def format_bytes(bytes_value):
    """
    Convert bytes to human readable format.
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"


def sanitize_input(value):
    """
    Sanitize user input by stripping tags and whitespace.
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    
    return value


def rate_limit_key(request, group, key_func=None):
    """
    Generate rate limiting key for requests.
    """
    if key_func:
        key = key_func(request)
    else:
        key = get_client_ip(request)
    
    return f"rate_limit_{group}_{key}"


def send_discord_webhook(webhook_url, message, username="HexAUTH"):
    """
    Send message to Discord webhook.
    """
    try:
        payload = {
            "content": message,
            "username": username
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 204
    except Exception as e:
        logger.error(f"Discord webhook failed: {e}")
        return False


def time_until_expiry(expiry_timestamp):
    """
    Calculate time until expiry in human readable format.
    """
    if not expiry_timestamp:
        return "Never"
    
    now = timezone.now()
    if isinstance(expiry_timestamp, int):
        expiry_dt = timezone.datetime.fromtimestamp(expiry_timestamp, tz=timezone.utc)
    else:
        expiry_dt = expiry_timestamp
    
    if expiry_dt <= now:
        return "Expired"
    
    delta = expiry_dt - now
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years != 1 else ''}"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months != 1 else ''}"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''}"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return f"{delta.seconds} second{'s' if delta.seconds != 1 else ''}"