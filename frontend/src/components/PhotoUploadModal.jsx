import React, { useState, useRef } from 'react';
import { X, Camera, Upload, CheckCircle2, AlertCircle, Sparkles, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

export default function PhotoUploadModal({ isOpen, onClose, token, onUploadStarted }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [showTips, setShowTips] = useState(false);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileSelected = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setErrorMsg('');
    startAsyncUpload(file);
  };

  const startAsyncUpload = async (file) => {
    setUploading(true);
    setErrorMsg('');

    const formData = new FormData();
    formData.append('photo', file);

    try {
      const res = await fetch('/api/upload-scale-photo/async', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to upload photo.');
      }

      // Notify parent app of background job started
      onUploadStarted(data.job_id);

      // Close modal smoothly
      setTimeout(() => {
        handleClose();
      }, 400);

    } catch (err) {
      console.error('Upload error:', err);
      setErrorMsg(err.message || 'Upload failed. Please check your connection.');
      setUploading(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setUploading(false);
    setErrorMsg('');
    setShowTips(false);
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" style={{ maxWidth: '520px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Camera size={20} style={{ color: 'var(--brand-purple)' }} />
            Scan Scale Photo
          </h3>
          <button className="close-btn" onClick={handleClose}>
            <X size={20} />
          </button>
        </div>

        {errorMsg && (
          <div style={{
            background: 'rgba(225, 29, 72, 0.08)',
            border: '1px solid rgba(225, 29, 72, 0.2)',
            borderRadius: '8px',
            padding: '10px 14px',
            marginBottom: '16px',
            fontSize: '13px',
            color: 'var(--brand-rose)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Upload Container */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div
            className="dropzone-box"
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files?.[0]) handleFileSelected(e.dataTransfer.files[0]);
            }}
          >
            {uploading ? (
              <div style={{ padding: '20px 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                <Sparkles size={32} className="animate-spin" style={{ color: 'var(--brand-purple)' }} />
                <p style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
                  Uploading & Starting Gemini Flash Vision...
                </p>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Your dashboard will update automatically in the background.
                </p>
              </div>
            ) : (
              <>
                <div className="dropzone-icon">
                  <Upload size={28} />
                </div>
                <p style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)', marginBottom: '4px' }}>
                  Click to upload or drag scale photo here
                </p>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  Processed asynchronously with Google Gemini Flash Vision & EXIF timestamps
                </p>
              </>
            )}
          </div>

          {/* Quick Buttons */}
          {!uploading && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ flex: 1, padding: '12px' }}
                onClick={() => cameraInputRef.current?.click()}
              >
                <Camera size={18} style={{ color: 'var(--brand-purple)' }} />
                Take Photo with Camera
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                style={{ flex: 1, padding: '12px' }}
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload size={18} />
                Browse Files
              </button>
            </div>
          )}

          {/* Tips Accordion */}
          <div style={{
            background: '#f8fafc',
            border: '1px solid var(--border-light)',
            borderRadius: 'var(--radius-md)',
            overflow: 'hidden'
          }}>
            <button
              type="button"
              onClick={() => setShowTips(!showTips)}
              style={{
                width: '100%',
                padding: '10px 14px',
                background: 'none',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
                fontWeight: 600,
                fontSize: '12px',
                color: 'var(--text-secondary)'
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <HelpCircle size={14} style={{ color: 'var(--brand-purple)' }} />
                Tips for Best Scale Photos
              </span>
              {showTips ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {showTips && (
              <div style={{ padding: '0 14px 12px', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                <ul style={{ paddingLeft: '18px', margin: 0 }}>
                  <li><strong>Center Display:</strong> Keep the digital screen in focus.</li>
                  <li><strong>Reduce Glare:</strong> Tilt phone slightly (10°–15°) if overhead lights reflect on the glass.</li>
                  <li><strong>Automatic Backdating:</strong> Photo capture time is read from EXIF metadata.</li>
                </ul>
              </div>
            )}
          </div>

          {/* Hidden inputs */}
          <input
            type="file"
            ref={fileInputRef}
            accept="image/*"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
          />
          <input
            type="file"
            ref={cameraInputRef}
            accept="image/*"
            capture="environment"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
          />
        </div>
      </div>
    </div>
  );
}
