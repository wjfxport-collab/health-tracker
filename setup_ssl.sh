#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERTS_DIR="$PROJECT_DIR/certs"
mkdir -p "$CERTS_DIR"

echo "=================================================================="
echo " 🔒 HealthPulse SSL & Let's Encrypt Certificate Setup            "
echo "=================================================================="

DOMAIN=""
EMAIL=""
MODE=""

# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --domain) DOMAIN="$2"; shift ;;
    --email) EMAIL="$2"; shift ;;
    --self-signed) MODE="self-signed" ;;
    --letsencrypt) MODE="letsencrypt" ;;
    --renew) MODE="renew" ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

# If renew mode requested
if [ "$MODE" = "renew" ]; then
  echo "-> Running Let's Encrypt renewal check..."
  if command -v certbot &> /dev/null; then
    sudo certbot renew --dry-run
    echo "✅ Renewal dry-run successful."
  else
    echo "❌ Certbot is not installed. Install via: sudo apt install certbot"
  fi
  exit 0
fi

# Self-signed mode
if [ "$MODE" = "self-signed" ] || [ -z "$DOMAIN" ]; then
  echo "-> Generating self-signed SSL certificate for local HTTPS / LAN testing..."
  "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/backend/ssl_manager.py"
  echo ""
  echo "✅ Self-signed SSL certificate generated in $CERTS_DIR"
  echo "👉 HTTPS is now ready for WebAuthn / Passkeys / Biometric logins on localhost & LAN."
  exit 0
fi

# Let's Encrypt mode
if [ -n "$DOMAIN" ]; then
  echo "-> Setting up Let's Encrypt SSL certificate for $DOMAIN..."
  
  if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    sudo apt update && sudo apt install -y certbot || sudo dnf install -y certbot || true
  fi

  EMAIL_ARG="--register-unsafely-without-email"
  if [ -n "$EMAIL" ]; then
    EMAIL_ARG="--email $EMAIL --no-eff-email"
  fi

  echo "-> Requesting certificate from Let's Encrypt..."
  sudo certbot certonly --standalone -d "$DOMAIN" $EMAIL_ARG --agree-tos --non-interactive || {
    echo "⚠️ Standalone certbot failed (port 80 may be in use). Trying webroot/manual..."
    sudo certbot certonly --webroot -w "$PROJECT_DIR/frontend/dist" -d "$DOMAIN" $EMAIL_ARG --agree-tos || true
  }

  LETSENCRYPT_PATH="/etc/letsencrypt/live/$DOMAIN"
  if [ -d "$LETSENCRYPT_PATH" ]; then
    echo "-> Linking Let's Encrypt certificates to $CERTS_DIR..."
    sudo ln -sf "$LETSENCRYPT_PATH/fullchain.pem" "$CERTS_DIR/cert.pem"
    sudo ln -sf "$LETSENCRYPT_PATH/privkey.pem" "$CERTS_DIR/key.pem"
    sudo chmod 644 "$CERTS_DIR/cert.pem" 2>/dev/null || true
    sudo chmod 600 "$CERTS_DIR/key.pem" 2>/dev/null || true

    # Automated renewal cronjob setup
    echo "-> Configuring automated certificate renewal cronjob..."
    CRON_CMD="0 3 * * * certbot renew --quiet --post-hook 'kill -HUP \$(pgrep -f backend/app.py) 2>/dev/null || true'"
    (crontab -l 2>/dev/null | grep -v "certbot renew" ; echo "$CRON_CMD") | crontab - 2>/dev/null || true
    echo "✅ Automated 90-day renewal cronjob scheduled (runs daily at 3:00 AM)."

    echo ""
    echo "🎉 Let's Encrypt SSL Certificate successfully installed for https://$DOMAIN!"
  else
    echo "❌ Certificate generation did not complete. Falling back to self-signed cert for now..."
    "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/backend/ssl_manager.py"
  fi
fi
