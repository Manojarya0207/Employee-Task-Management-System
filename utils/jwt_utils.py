import hmac
import hashlib
import base64
import json
import time
from config import STORAGE_SECRET

def sign_token(payload: dict, expiry_seconds: int = 86400) -> str:
    """Signs a payload into a secure HMAC token."""
    payload = dict(payload)
    payload['exp'] = int(time.time()) + expiry_seconds
    
    # Base64 encode payload
    payload_json = json.dumps(payload).encode('utf-8')
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode('utf-8').rstrip('=')
    
    # Generate signature
    signature = hmac.new(
        STORAGE_SECRET.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{payload_b64}.{signature_b64}"

def verify_token(token: str) -> dict | None:
    """Verifies an HMAC token and returns the payload if valid."""
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
            
        payload_b64, signature_b64 = parts
        
        # Verify signature
        expected_signature = hmac.new(
            STORAGE_SECRET.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None
            
        # Decode payload
        padding = '=' * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode('utf-8')
        payload = json.loads(payload_json)
        
        # Check expiry
        if payload.get('exp', 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None
