import os
import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import ipaddress

CERTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'certs')

def ensure_certs_dir():
    os.makedirs(CERTS_DIR, exist_ok=True)
    return CERTS_DIR

def get_ssl_cert_paths():
    """
    Check for existing SSL certificates (Let's Encrypt or local certs).
    Returns (cert_path, key_path) or (None, None).
    """
    custom_cert = os.environ.get('SSL_CERT_PATH')
    custom_key = os.environ.get('SSL_KEY_PATH')
    if custom_cert and custom_key and os.path.exists(custom_cert) and os.path.exists(custom_key):
        return custom_cert, custom_key

    local_cert = os.path.join(CERTS_DIR, 'cert.pem')
    local_key = os.path.join(CERTS_DIR, 'key.pem')
    if os.path.exists(local_cert) and os.path.exists(local_key):
        return local_cert, local_key

    return None, None

def generate_self_signed_cert(hostname="localhost"):
    """
    Generate self-signed SSL certificate with SANs (localhost, 127.0.0.1, LAN IP)
    for secure local testing of WebAuthn and Passkeys over HTTPS.
    """
    ensure_certs_dir()
    cert_path = os.path.join(CERTS_DIR, 'cert.pem')
    key_path = os.path.join(CERTS_DIR, 'key.pem')

    # Generate Private Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "CA"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HealthPulse Local Dev"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])

    # Subject Alternative Names (SANs)
    alt_names = [
        x509.DNSName(hostname),
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ]

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    # Write Key
    with open(key_path, "wb") as f:
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    # Write Certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"✅ Generated SSL Certificate: {cert_path}")
    print(f"✅ Generated Private Key: {key_path}")
    return cert_path, key_path

if __name__ == '__main__':
    generate_self_signed_cert()
