import React, { useState, useRef } from 'react';
import { X, Camera, Upload, CheckCircle2, AlertCircle, Calendar, Scale, Footprints, Sparkles, Clock, RefreshCw, FileText, HelpCircle, ChevronDown, ChevronUp, Cpu, Server } from 'lucide-react';

export default function PhotoUploadModal({ isOpen, onClose, onEntrySaved, defaultUnit }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [showTips, setShowTips] = useState(false);
  
  // Form fields for review & confirmation
  const [date, setDate] = useState('');
  const [weight, setWeight] = useState('');
  const [steps, setSteps] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  if (!isOpen) return null;

  const handleFileChange = (file) => {
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    setScanResult(null);
    setErrorMsg('');
    startOCRScan(file);
  };

  const startOCRScan = async (file) => {
    setScanning(true);
    setErrorMsg('');
    
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('save_immediately', 'false');

    try {
      const res = await fetch('/api/upload-scale-photo', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      setScanResult(data);

      // Pre-fill editable fields
      if (data.date) setDate(data.date);
      if (data.weight) setWeight(data.weight);
      setNotes(data.notes || (data.exif_found ? `Scale photo (captured ${data.time || ''})` : 'Scale photo'));

      if (!data.success && data.error) {
        setErrorMsg(data.error);
      }
    } catch (err) {
      console.error('Scan error:', err);
      setErrorMsg('Failed to process image. Please check your connection and try again.');
      setScanResult({ success: false, date: new Date().toISOString().split('T')[0], exif_found: false });
      setDate(new Date().toISOString().split('T')[0]);
    } finally {
      setScanning(false);
    }
  };

  const handleSaveConfirmed = async (e) => {
    e.preventDefault();
    if (!date) {
      setErrorMsg('Date is required.');
      return;
    }
    if (weight === '') {
      setErrorMsg('Please enter a weight value.');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch('/api/entries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date,
          weight: parseFloat(weight),
          steps: steps !== '' ? parseInt(steps, 10) : null,
          notes
        })
      });

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to save entry');
      }

      await onEntrySaved();
      handleClose();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to save entry.');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setScanning(false);
    setScanResult(null);
    setErrorMsg('');
    setShowTips(false);
    onClose();
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setScanResult(null);
    setErrorMsg('');
  };

  const isGeminiEngine = scanResult?.engine?.includes('gemini');
  const isLocalGemmaEngine = scanResult?.engine?.includes('gemma') || scanResult?.engine?.includes('192.168');

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" style={{ maxWidth: '600px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Camera size={20} style={{ color: 'var(--brand-purple)' }} />
            Scan Bathroom Scale Photo
          </h3>
          <button className="close-btn" onClick={handleClose}>
            <X size={20} />
          </button>
        </div>

        {/* Step 1: Upload / Capture view */}
        {!selectedFile && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div
              className="dropzone-box"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
              }}
            >
              <div className="dropzone-icon">
                <Upload size={28} />
              </div>
              <p style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)', marginBottom: '4px' }}>
                Click to upload or drag scale photo here
              </p>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                Supports Gemini Cloud, Local Mac Gemma (192.168.4.27), or Tesseract
              </p>
            </div>

            {/* Mobile Camera Direct Button */}
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
                Browse Photo Library
              </button>
            </div>

            {/* Photo Quality & Lighting Tips Accordion */}
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
                  padding: '12px 16px',
                  background: 'none',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '13px',
                  color: 'var(--text-secondary)'
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <HelpCircle size={15} style={{ color: 'var(--brand-purple)' }} />
                  Tips for Best Accuracy
                </span>
                {showTips ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showTips && (
                <div style={{ padding: '0 16px 14px', fontSize: '12px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  <ul style={{ paddingLeft: '18px', margin: 0 }}>
                    <li><strong>Framing:</strong> Center the LCD display in the photo.</li>
                    <li><strong>Glare:</strong> If ceiling lights reflect on the glass, tilt your phone slightly (10°–15°).</li>
                    <li><strong>Exposure:</strong> Tap the screen on the numbers and lower the brightness slider slightly to prevent backlight bloom.</li>
                  </ul>
                </div>
              )}
            </div>

            {/* Hidden native inputs */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
            />
            <input
              type="file"
              ref={cameraInputRef}
              accept="image/*"
              capture="environment"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
            />
          </div>
        )}

        {/* Step 2: Processing & Result review */}
        {selectedFile && (
          <div>
            {/* Image Preview & Scanning Laser */}
            <div className="photo-preview-container">
              <img src={previewUrl} alt="Scale Display" className="photo-preview-img" />
              
              {scanning && (
                <div className="scanning-overlay">
                  <div className="scanner-laser"></div>
                  <div className="scanning-badge">
                    <Sparkles size={16} className="animate-spin" />
                    Vision AI Analyzing Display & Extracting EXIF Timestamp...
                  </div>
                </div>
              )}

              {!scanning && (
                <button className="photo-retake-btn" onClick={handleReset} title="Upload different photo">
                  <RefreshCw size={14} /> Retake
                </button>
              )}
            </div>

            {/* Scanning Status & Feedback */}
            {!scanning && scanResult && (
              <div style={{ marginTop: '16px' }}>
                {scanResult.success ? (
                  <div className="ocr-status-card ocr-success">
                    <CheckCircle2 size={20} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '6px' }}>
                        <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                          Detected: <strong>{scanResult.weight} {scanResult.unit || defaultUnit}</strong>
                        </span>
                        
                        {/* Engine Badge */}
                        <span className="badge" style={{
                          background: isLocalGemmaEngine ? '#eff6ff' : isGeminiEngine ? 'var(--brand-purple-subtle)' : 'var(--bg-subtle)',
                          color: isLocalGemmaEngine ? 'var(--brand-blue)' : isGeminiEngine ? 'var(--brand-purple)' : 'var(--text-secondary)',
                          border: `1px solid ${isLocalGemmaEngine ? 'var(--brand-blue-border)' : isGeminiEngine ? 'var(--brand-purple-border)' : 'var(--border-light)'}`,
                          fontSize: '11px'
                        }}>
                          {isLocalGemmaEngine ? (
                            <><Server size={11} /> Gemma 4 12B (Mac)</>
                          ) : isGeminiEngine ? (
                            <><Sparkles size={11} /> Gemini 2.5 Flash</>
                          ) : (
                            <><Cpu size={11} /> Local OCR</>
                          )}
                        </span>
                      </div>

                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {scanResult.exif_found ? (
                          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <Clock size={12} /> Extracted photo timestamp: <strong>{scanResult.date} at {scanResult.time}</strong>
                          </span>
                        ) : (
                          <span>Photo date metadata not found; defaulted to today</span>
                        )}
                      </div>

                      {scanResult.notes && (
                        <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', fontStyle: 'italic' }}>
                          "{scanResult.notes}"
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="ocr-status-card ocr-warning">
                    <AlertCircle size={20} style={{ color: 'var(--brand-amber)', flexShrink: 0 }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--text-primary)' }}>
                        Could not clearly isolate scale numbers
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        {scanResult.exif_found && (
                          <span>Photo timestamp found: <strong>{scanResult.date} ({scanResult.time})</strong>. </span>
                        )}
                        Please check your photo and type the weight below:
                      </div>
                      {scanResult.error && (
                        <div style={{ fontSize: '11px', color: 'var(--brand-amber)', marginTop: '4px' }}>
                          {scanResult.error}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Form to Confirm & Edit */}
                <form onSubmit={handleSaveConfirmed} style={{ marginTop: '16px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    {/* Date */}
                    <div className="form-group">
                      <label className="form-label">
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                          <Calendar size={14} /> Date {scanResult.exif_found && '(from Photo)'}
                        </span>
                      </label>
                      <input
                        type="date"
                        className="form-input"
                        value={date}
                        onChange={(e) => setDate(e.target.value)}
                        required
                      />
                    </div>

                    {/* Weight */}
                    <div className="form-group">
                      <label className="form-label">
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                          <Scale size={14} /> Weight ({defaultUnit || 'lbs'})
                        </span>
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        placeholder="e.g. 208.4"
                        className="form-input"
                        value={weight}
                        onChange={(e) => setWeight(e.target.value)}
                        required
                        autoFocus={!scanResult.success}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    {/* Optional Steps */}
                    <div className="form-group">
                      <label className="form-label">
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                          <Footprints size={14} /> Steps (optional)
                        </span>
                      </label>
                      <input
                        type="number"
                        placeholder="e.g. 8500"
                        className="form-input"
                        value={steps}
                        onChange={(e) => setSteps(e.target.value)}
                      />
                    </div>

                    {/* Notes */}
                    <div className="form-group">
                      <label className="form-label">
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px' }}>
                          <FileText size={14} /> Notes
                        </span>
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Morning weigh-in"
                        className="form-input"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
                    <button type="button" className="btn btn-secondary" onClick={handleClose}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary" disabled={saving}>
                      <CheckCircle2 size={16} />
                      {saving ? 'Saving...' : 'Confirm & Save Entry'}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
