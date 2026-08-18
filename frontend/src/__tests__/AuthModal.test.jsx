import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import AuthModal from '../components/AuthModal';

describe('AuthModal Component', () => {
  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <AuthModal isOpen={false} onClose={() => {}} onAuthSuccess={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders sign-in form with username, password, and passkey button when open', () => {
    render(
      <AuthModal isOpen={true} onClose={() => {}} onAuthSuccess={() => {}} />
    );

    expect(screen.getByText(/Sign In to HealthPulse/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. alex')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByText(/Sign in with Touch ID \/ Face ID \/ Passkey/i)).toBeInTheDocument();
  });

  it('switches to Register tab and displays Confirm Password field', () => {
    render(
      <AuthModal isOpen={true} onClose={() => {}} onAuthSuccess={() => {}} />
    );

    const registerTab = screen.getByRole('button', { name: /^Register$/i });
    fireEvent.click(registerTab);

    expect(screen.getByText(/Create HealthPulse Account/i)).toBeInTheDocument();
    expect(screen.getByText(/Confirm Password/i)).toBeInTheDocument();
  });

  it('validates password mismatch on registration', async () => {
    render(
      <AuthModal isOpen={true} onClose={() => {}} onAuthSuccess={() => {}} />
    );

    // Switch to register tab
    fireEvent.click(screen.getByRole('button', { name: /^Register$/i }));

    const usernameInput = screen.getByPlaceholderText('e.g. alex');
    const passwordInputs = screen.getAllByPlaceholderText('••••••••');

    fireEvent.change(usernameInput, { target: { value: 'alex_test' } });
    fireEvent.change(passwordInputs[0], { target: { value: 'password123' } });
    fireEvent.change(passwordInputs[1], { target: { value: 'passwordMismatch' } });

    const submitBtn = screen.getByRole('button', { name: /Create Account/i });
    fireEvent.click(submitBtn);

    expect(await screen.findByText(/Passwords do not match/i)).toBeInTheDocument();
  });
});
