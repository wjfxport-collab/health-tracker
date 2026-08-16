import React, { useState, useEffect } from 'react';
import { X, Target, Save, Check, Sparkles, Eye, EyeOff, ExternalLink, Cpu, Server, Wifi, AlertCircle, RefreshCw } from 'lucide-react';

export default function GoalSettings({ isOpen, onClose, goals, onSaveGoals }) {
  const [stepGoal, setStepGoal] = useState(10000);
  const [targetWeight, setTargetWeight] = useState(165);
  const [startingWeight, setStartingWeight] = useState(185);
  const [unit, setUnit] = useState('lbs');
  
  // AI Vision Settings
  const [ocrEngine, setOcrEngine] = useState('gemini'); // 'gemini' | 'local_llm' | 'local'
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [localLlmUrl, setLocalLlmUrl] = useState('http://192.168.4.27:11434');
  const [localLlmModel, setLocalLlmModel] = useState('gemma-4-12b');

  // Connection testing state
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (goals) {
      setStepGoal(goals.daily_steps_goal || 10000);
      setTargetWeight(goals.target_weight || 165);
      setStartingWeight(goals.starting_weight || 185);
      setUnit(goals.weight_unit || 'lbs');
      setGeminiApiKey(goals.gemini_api_key || '');
      setOcrEngine(goals.ocr_engine || 'gemini');
      setLocalLlmUrl(goals.local_llm_url || 'http://192.168.4.27:11434');
      setLocalLlmModel(goals.local_llm_model || 'gemma-4-12b');
    }
    setSavedSuccess(false);
    setTestResult(null);
  }, [goals, isOpen]);

  if (!isOpen) return null;

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const res = await fetch('/api/test-local-llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ server_url: localLlmUrl.trim() })
      });
      const data = await res.json();
      setTestResult(data);
    } catch (err) {
      setTestResult({ success: false, message: 'Could not connect to test endpoint: ' + err.message });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSaveGoals({
        daily_steps_goal: parseInt(stepGoal, 10),
        target_weight: parseFloat(targetWeight),
        starting_weight: parseFloat(startingWeight),
        weight_unit: unit,
        gemini_api_key: geminiApiKey.trim(),
        ocr_engine: ocrEngine,
        local_llm_url: localLlmUrl.trim(),
        local_llm_model: localLlmModel.trim()
      });
      setSavedSuccess(true);
      setTimeout(() => {
        onClose();
      }, 700);
    } catch (err) {
      alert('Error updating settings: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" style={{ maxWidth: '580px' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Target size={20} style={{ color: 'var(--brand-primary)' }} />
            Goals & Vision AI Settings
          </h3>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Fitness Targets Section */}
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
              Fitness Targets
            </h4>

            {/* Weight Unit */}
            <div className="form-group">
              <label className="form-label">Preferred Unit</label>
              <div style={{ display: 'flex', gap: '16px' }}>
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '14px' }}>
                  <input
                    type="radio"
                    name="unit"
                    value="lbs"
                    checked={unit === 'lbs'}
                    onChange={(e) => setUnit(e.target.value)}
                  />
                  Pounds (lbs)
                </label>
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer', fontSize: '14px' }}>
                  <input
                    type="radio"
                    name="unit"
                    value="kg"
                    checked={unit === 'kg'}
                    onChange={(e) => setUnit(e.target.value)}
                  />
                  Kilograms (kg)
                </label>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {/* Daily Steps Goal */}
              <div className="form-group">
                <label className="form-label">Daily Step Goal</label>
                <input
                  type="number"
                  step="500"
                  className="form-input"
                  value={stepGoal}
                  onChange={(e) => setStepGoal(e.target.value)}
                  required
                />
              </div>

              {/* Target Weight */}
              <div className="form-group">
                <label className="form-label">Target Weight ({unit})</label>
                <input
                  type="number"
                  step="0.1"
                  className="form-input"
                  value={targetWeight}
                  onChange={(e) => setTargetWeight(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Starting Weight */}
            <div className="form-group">
              <label className="form-label">Starting Weight ({unit})</label>
              <input
                type="number"
                step="0.1"
                className="form-input"
                value={startingWeight}
                onChange={(e) => setStartingWeight(e.target.value)}
                required
              />
            </div>
          </div>

          {/* AI Vision Engine Selection Section */}
          <div style={{
            background: '#f8fafc',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-md)',
            padding: '16px',
            marginBottom: '20px'
          }}>
            <h4 style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={16} style={{ color: 'var(--brand-purple)' }} />
              Scale Photo Vision Engine
            </h4>

            {/* 3-Way Engine Selector */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '14px' }}>
              {/* Option 1: Gemini Cloud */}
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                background: ocrEngine === 'gemini' ? 'var(--brand-purple-subtle)' : '#ffffff',
                border: `1px solid ${ocrEngine === 'gemini' ? 'var(--brand-purple-border)' : 'var(--border-light)'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}>
                <input
                  type="radio"
                  name="ocr_engine"
                  value="gemini"
                  checked={ocrEngine === 'gemini'}
                  onChange={(e) => setOcrEngine(e.target.value)}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>
                    Google Gemini 2.5 Flash Vision (Cloud)
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Fastest cloud LLM with 99%+ accuracy on tricky 7-segment digital screens
                  </div>
                </div>
              </label>

              {/* Option 2: Local Mac Gemma 4 12B */}
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                background: ocrEngine === 'local_llm' ? '#eff6ff' : '#ffffff',
                border: `1px solid ${ocrEngine === 'local_llm' ? 'var(--brand-blue-border)' : 'var(--border-light)'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}>
                <input
                  type="radio"
                  name="ocr_engine"
                  value="local_llm"
                  checked={ocrEngine === 'local_llm'}
                  onChange={(e) => setOcrEngine(e.target.value)}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>
                    Local Mac Gemma 4 12B Vision (LAN: 192.168.4.27)
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Private local network LLM server running on your Mac
                  </div>
                </div>
              </label>

              {/* Option 3: Local Tesseract OCR */}
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 12px',
                background: ocrEngine === 'local' ? 'var(--bg-subtle)' : '#ffffff',
                border: `1px solid ${ocrEngine === 'local' ? 'var(--border-medium)' : 'var(--border-light)'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}>
                <input
                  type="radio"
                  name="ocr_engine"
                  value="local"
                  checked={ocrEngine === 'local'}
                  onChange={(e) => setOcrEngine(e.target.value)}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '13px', color: 'var(--text-primary)' }}>
                    Local Tesseract OCR (Offline Fallback)
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    On-device OCR without requiring an LLM or network connection
                  </div>
                </div>
              </label>
            </div>

            {/* Dynamic Settings Area: Gemini API Key */}
            {ocrEngine === 'gemini' && (
              <div style={{ background: '#ffffff', padding: '12px', borderRadius: '8px', border: '1px solid var(--brand-purple-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <label className="form-label" style={{ fontSize: '12px', margin: 0 }}>
                    Google Gemini API Key
                  </label>
                  <a
                    href="https://aistudio.google.com/app/apikey"
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '11px', color: 'var(--brand-purple)', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '3px' }}
                  >
                    Get Free Key <ExternalLink size={10} />
                  </a>
                </div>
                <div style={{ position: 'relative' }}>
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    placeholder="AIzaSy..."
                    className="form-input"
                    style={{ paddingRight: '40px', fontSize: '13px' }}
                    value={geminiApiKey}
                    onChange={(e) => setGeminiApiKey(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    style={{
                      position: 'absolute',
                      right: '10px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: 'var(--text-muted)'
                    }}
                  >
                    {showApiKey ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>
            )}

            {/* Dynamic Settings Area: Local Mac Gemma Config */}
            {ocrEngine === 'local_llm' && (
              <div style={{ background: '#ffffff', padding: '12px', borderRadius: '8px', border: '1px solid var(--brand-blue-border)' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px', marginBottom: '8px' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '11px', margin: '0 0 4px' }}>
                      Mac Server URL (e.g. Ollama / vLLM / LM Studio)
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '13px' }}
                      value={localLlmUrl}
                      onChange={(e) => setLocalLlmUrl(e.target.value)}
                      placeholder="http://192.168.4.27:11434"
                      required
                    />
                  </div>

                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: '11px', margin: '0 0 4px' }}>
                      Model Name
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      style={{ fontSize: '13px' }}
                      value={localLlmModel}
                      onChange={(e) => setLocalLlmModel(e.target.value)}
                      placeholder="gemma-4-12b"
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '10px' }}>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={handleTestConnection}
                    disabled={testingConnection}
                  >
                    <Wifi size={13} />
                    {testingConnection ? 'Testing...' : 'Test Connection to Mac'}
                  </button>

                  {testResult && (
                    <div style={{
                      fontSize: '11px',
                      fontWeight: 600,
                      color: testResult.success ? 'var(--brand-primary)' : 'var(--brand-rose)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}>
                      {testResult.success ? <Check size={13} /> : <AlertCircle size={13} />}
                      {testResult.message}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '20px' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading || savedSuccess}>
              {savedSuccess ? (
                <>
                  <Check size={16} /> Saved!
                </>
              ) : (
                <>
                  <Save size={16} /> {loading ? 'Saving...' : 'Save Settings'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
