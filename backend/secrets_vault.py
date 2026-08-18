import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from config import settings

def _derive_fernet_key(secret: str) -> bytes:
    """
    Ensure the secret is a valid 32-byte urlsafe base64-encoded key for Fernet.
    """
    if not secret:
        secret = "healthpulse-default-fallback-key-2026"
    
    try:
        # Check if already a valid 32-byte base64 key
        decoded = base64.urlsafe_b64decode(secret)
        if len(decoded) == 32:
            return secret.encode('utf-8')
    except Exception:
        pass

    # Derive deterministic 32-byte key using SHA-256
    digest = hashlib.sha256(secret.encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)

# Initialize Fernet cipher with configured SECRET_KEY
_FERNET_KEY = _derive_fernet_key(settings.SECRET_KEY)
_cipher = Fernet(_FERNET_KEY)

# Encryption prefix identifier to distinguish ciphertext from legacy plaintext
CIPHER_PREFIX = "enc:v1:"

def encrypt_secret(plaintext: str) -> str:
    """
    Encrypt a sensitive credential string (e.g. Gemini API key).
    Returns a prefixed ciphertext string suitable for database storage.
    """
    if not plaintext:
        return ""
    plaintext_str = str(plaintext).strip()
    if not plaintext_str:
        return ""

    # If already encrypted, return as is
    if plaintext_str.startswith(CIPHER_PREFIX):
        return plaintext_str

    token = _cipher.encrypt(plaintext_str.encode('utf-8')).decode('utf-8')
    return f"{CIPHER_PREFIX}{token}"

def decrypt_secret(stored_val: str) -> str:
    """
    Decrypt a stored credential.
    If the value was stored as unencrypted plaintext (legacy), returns it directly.
    """
    if not stored_val:
        return ""
    stored_str = str(stored_val).strip()
    if not stored_str:
        return ""

    if not stored_str.startswith(CIPHER_PREFIX):
        # Legacy unencrypted plaintext fallback
        return stored_str

    try:
        raw_token = stored_str[len(CIPHER_PREFIX):]
        decrypted = _cipher.decrypt(raw_token.encode('utf-8')).decode('utf-8')
        return decrypted
    except (InvalidToken, Exception) as e:
        print(f"Warning: Failed to decrypt credential token: {e}")
        return ""

def mask_secret(secret_str: str) -> str:
    """
    Helper to mask an API key for safe UI display (e.g. AIzaSy...4x).
    """
    if not secret_str:
        return ""
    s = secret_str.strip()
    if len(s) <= 8:
        return "••••••••"
    return f"{s[:6]}...{s[-4:]}"
