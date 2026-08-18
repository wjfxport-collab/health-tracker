import { describe, it, expect } from 'vitest';
import { bufferToBase64Url, base64UrlToBuffer, isBiometricAvailable } from '../utils/webauthn';

describe('WebAuthn Utility Functions', () => {
  it('converts ArrayBuffer to Base64URL string and back accurately', () => {
    const originalText = 'HealthPulse-Passkey-Test-2026';
    const encoder = new TextEncoder();
    const decoder = new TextDecoder();

    const buffer = encoder.encode(originalText).buffer;
    const b64url = bufferToBase64Url(buffer);

    expect(typeof b64url).toBe('string');
    expect(b64url).not.toContain('+');
    expect(b64url).not.toContain('/');
    expect(b64url).not.toContain('=');

    const decodedBuffer = base64UrlToBuffer(b64url);
    const decodedText = decoder.decode(decodedBuffer);

    expect(decodedText).toBe(originalText);
  });

  it('detects biometric availability safely without errors', async () => {
    const isAvail = await isBiometricAvailable();
    expect(typeof isAvail).toBe('boolean');
  });
});
