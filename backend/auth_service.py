import os
import time
import json
import base64
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from config import settings

JWT_SECRET = settings.JWT_SECRET
RP_NAME = settings.RP_NAME
RP_ID = settings.RP_ID

# In-memory challenge store (maps challenge_id -> {challenge, user_id, expires_at})
CHALLENGES = {}

def cleanup_challenges():
    now = time.time()
    expired = [k for k, v in CHALLENGES.items() if v.get('expires_at', 0) < now]
    for k in expired:
        CHALLENGES.pop(k, None)

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def b64url_decode(s: str) -> bytes:
    padding = '=' * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)

# --- Password Utilities ---

def hash_user_password(password: str) -> str:
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_user_password(password_hash: str, password: str) -> bool:
    if not password_hash:
        return False
    return check_password_hash(password_hash, password)

# --- JWT Token Utilities ---

def create_access_token(user_id: int, username: str, expires_in_hours: int = 72) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user_id),
        'username': username,
        'iat': now,
        'exp': now + timedelta(hours=expires_in_hours)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except Exception:
        return None

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1].strip()
        elif request.cookies.get('auth_token'):
            token = request.cookies.get('auth_token')

        if not token:
            return jsonify({'success': False, 'error': 'Authentication required. Please sign in.'}), 401

        payload = decode_access_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired session. Please sign in again.'}), 401

        request.current_user = {
            'id': int(payload['sub']),
            'username': payload['username']
        }
        return f(*args, **kwargs)
    return decorated

# --- WebAuthn / Passkey / Biometric Handlers ---

def create_registration_challenge(user_id: int, username: str):
    cleanup_challenges()
    challenge_bytes = secrets.token_bytes(32)
    challenge_b64 = b64url_encode(challenge_bytes)
    
    CHALLENGES[challenge_b64] = {
        'user_id': user_id,
        'username': username,
        'type': 'registration',
        'expires_at': time.time() + 300
    }

    options = {
        "challenge": challenge_b64,
        "rp": {
            "name": RP_NAME,
            "id": request.host.split(':')[0] if request else RP_ID
        },
        "user": {
            "id": b64url_encode(str(user_id).encode('utf-8')),
            "name": username,
            "displayName": username
        },
        "pubKeyCredParams": [
            {"alg": -7, "type": "public-key"},   # ES256 (NIST P-256) - Most common for Face ID/Touch ID
            {"alg": -257, "type": "public-key"}  # RS256 - Windows Hello/Yubikey
        ],
        "authenticatorSelection": {
            "authenticatorAttachment": "platform", # Biometric on device (Face ID, Touch ID, Fingerprint)
            "userVerification": "preferred",
            "residentKey": "preferred",
            "requireResidentKey": False
        },
        "timeout": 60000,
        "attestation": "none"
    }
    return options

def create_authentication_challenge(user_id: int = None, username: str = None):
    cleanup_challenges()
    challenge_bytes = secrets.token_bytes(32)
    challenge_b64 = b64url_encode(challenge_bytes)
    
    CHALLENGES[challenge_b64] = {
        'user_id': user_id,
        'username': username,
        'type': 'authentication',
        'expires_at': time.time() + 300
    }

    options = {
        "challenge": challenge_b64,
        "rpId": request.host.split(':')[0] if request else RP_ID,
        "timeout": 60000,
        "userVerification": "preferred"
    }
    return options

def verify_registration_challenge(challenge_b64: str) -> dict:
    cleanup_challenges()
    data = CHALLENGES.pop(challenge_b64, None)
    if not data or data.get('type') != 'registration':
        return None
    return data

def verify_authentication_challenge(challenge_b64: str) -> dict:
    cleanup_challenges()
    data = CHALLENGES.pop(challenge_b64, None)
    if not data or data.get('type') != 'authentication':
        return None
    return data
