import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import PhotoUploadModal from '../components/PhotoUploadModal';

describe('PhotoUploadModal Component', () => {
  it('renders nothing when isOpen is false', () => {
    const { container } = render(
      <PhotoUploadModal isOpen={false} onClose={() => {}} onUploadSuccess={() => {}} />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders async upload modal with camera option and file browse', () => {
    render(
      <PhotoUploadModal isOpen={true} onClose={() => {}} onUploadSuccess={() => {}} />
    );

    expect(screen.getByText(/Scan Scale Photo/i)).toBeInTheDocument();
    expect(screen.getByText(/Processed asynchronously with Google Gemini Flash Vision/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Take Photo with Camera/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Browse Files/i })).toBeInTheDocument();
  });

  it('triggers immediate async upload state upon file selection', () => {
    // Mock global fetch for async scale upload
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      text: () => Promise.stringify({ success: true, job_id: 101, status: 'processing' })
    });

    render(
      <PhotoUploadModal isOpen={true} onClose={() => {}} onUploadSuccess={() => {}} />
    );

    const file = new File(['dummy photo bytes'], 'scale_photo.jpg', { type: 'image/jpeg' });
    const fileInputs = document.querySelectorAll('input[type="file"]');
    expect(fileInputs.length).toBeGreaterThan(0);

    fireEvent.change(fileInputs[0], { target: { files: [file] } });

    // Should immediately display background processing indicator
    expect(screen.getByText(/Uploading & Starting Gemini Flash Vision.../i)).toBeInTheDocument();
  });
});
