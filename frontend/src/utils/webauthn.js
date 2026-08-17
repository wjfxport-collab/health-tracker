/**
 * WebAuthn & Passkey Client-Side Helpers
 * Supports Face ID, Touch ID, Windows Hello, and Platform Biometrics.
 */

// Base64URL string -> Uint8Array buffer
export function base64UrlToBuffer(base64Url) {
  const padding = '='.repeat((4 - (base64Url.length % 4)) % 4);
  const base64 = (base64Url + padding).replace(/\-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray.buffer;
}

// ArrayBuffer -> Base64URL string
export function bufferToBase64Url(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = window.btoa(binary);
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

/**
 * Check if the browser and device support biometric platform authenticators (Face ID / Touch ID)
 */
export async function isBiometricAvailable() {
  if (!window.PublicKeyCredential) return false;
  if (!window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable) return false;
  try {
    return await window.PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable();
  } catch (e) {
    return false;
  }
}

/**
 * Register a new Biometric Passkey for the currently logged-in user
 */
export async function registerPasskey(token, nickname = 'My Biometric Device') {
  // 1. Fetch challenge options from backend
  const res = await fetch('/api/auth/webauthn/register/options', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Failed to get passkey registration options');

  const options = data.options;
  options.challenge = base64UrlToBuffer(options.challenge);
  options.user.id = base64UrlToBuffer(options.user.id);

  // 2. Prompt native device biometric (Face ID / Touch ID)
  const credential = await navigator.credentials.create({
    publicKey: options
  });

  if (!credential) throw new Error('Passkey registration was cancelled or not supported.');

  // 3. Encode credential response
  const credentialId = bufferToBase64Url(credential.rawId);
  const clientDataJSON = bufferToBase64Url(credential.response.clientDataJSON);
  const attestationObject = bufferToBase64Url(credential.response.attestationObject);

  // 4. Send to backend for verification
  const verifyRes = await fetch('/api/auth/webauthn/register/verify', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      challenge: data.options.challenge,
      credential_id: credentialId,
      public_key: attestationObject,
      nickname: nickname || 'Biometric Device'
    })
  });

  const verifyData = await verifyRes.json();
  if (!verifyData.success) throw new Error(verifyData.error || 'Failed to verify passkey.');
  return verifyData;
}

/**
 * Authenticate with Biometric Passkey (Touch ID, Face ID, Windows Hello)
 */
export async function loginWithPasskey(username = '') {
  // 1. Get challenge from server
  const res = await fetch('/api/auth/webauthn/login/options', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: username.trim() })
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error || 'Failed to initiate passkey sign-in');

  const challengeB64 = data.options.challenge;
  const options = {
    ...data.options,
    challenge: base64UrlToBuffer(challengeB64)
  };

  // 2. Prompt native device authentication
  const assertion = await navigator.credentials.get({
    publicKey: options
  });

  if (!assertion) throw new Error('Biometric passkey authentication was cancelled.');

  const credentialId = bufferToBase64Url(assertion.rawId);
  const clientDataJSON = bufferToBase64Url(assertion.response.clientDataJSON);
  const authenticatorData = bufferToBase64Url(assertion.response.authenticatorData);
  const signature = bufferToBase64Url(assertion.response.signature);

  // 3. Verify signature on backend
  const verifyRes = await fetch('/api/auth/webauthn/login/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      challenge: challengeB64,
      credential_id: credentialId,
      client_data_json: clientDataJSON,
      authenticator_data: authenticatorData,
      signature: signature
    })
  });

  const verifyData = await verifyRes.json();
  if (!verifyData.success) throw new Error(verifyData.error || 'Passkey verification failed.');
  return verifyData;
}
