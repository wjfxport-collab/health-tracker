import React, { useState, useEffect, useCallback } from 'react';
import { Activity, Plus, Camera, Settings, RefreshCw, Sparkles, AlertTriangle, CheckCircle2, X, LogIn, User, ShieldCheck, LogOut } from 'lucide-react';
import MetricCards from './components/MetricCards';
import Charts from './components/Charts';
import HistoryTable from './components/HistoryTable';
import EntryForm from './components/EntryForm';
import GoalSettings from './components/GoalSettings';
import PhotoUploadModal from './components/PhotoUploadModal';
import AuthModal from './components/AuthModal';

export default function App() {
  // Auth state
  const [token, setToken] = useState(() => localStorage.getItem('healthpulse_token') || '');
  const [currentUser, setCurrentUser] = useState(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);

  // App data state
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [goals, setGoals] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals state
  const [entryModalOpen, setEntryModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [goalModalOpen, setGoalModalOpen] = useState(false);
  const [photoModalOpen, setPhotoModalOpen] = useState(false);

  // Async Scale Processing & Warning Banner State
  const [activeJobs, setActiveJobs] = useState([]);
  const [bannerAlert, setBannerAlert] = useState(null);
  const [successToast, setSuccessToast] = useState('');

  // Fetch Current User Profile
  const fetchUserProfile = useCallback(async (authToken) => {
    if (!authToken) {
      setCurrentUser(null);
      setLoading(false);
      return;
    }
    try {
      const res = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.status === 401) {
        // Token expired
        handleLogout();
        return;
      }
      const data = await res.json();
      if (data.success) {
        setCurrentUser(data.user);
      }
    } catch (err) {
      console.error('Failed to fetch user profile:', err);
    }
  }, []);

  // Fetch All Tracker Data
  const fetchData = useCallback(async () => {
    if (!token) return;
    try {
      setError(null);
      const headers = { 'Authorization': `Bearer ${token}` };

      const [entriesRes, statsRes, goalsRes, jobsRes] = await Promise.all([
        fetch('/api/entries', { headers }),
        fetch('/api/stats', { headers }),
        fetch('/api/goals', { headers }),
        fetch('/api/upload-scale-photo/status', { headers })
      ]);

      if (entriesRes.status === 401 || statsRes.status === 401) {
        handleLogout();
        return;
      }

      const entriesData = await entriesRes.json();
      const statsData = await statsRes.json();
      const goalsData = await goalsRes.json();
      const jobsData = await jobsRes.json();

      if (entriesData.success) setEntries(entriesData.entries || []);
      if (statsData.success) setStats(statsData.stats || null);
      if (goalsData.success) setGoals(goalsData.goals || null);

      if (jobsData.success && jobsData.jobs) {
        setActiveJobs(jobsData.jobs);
        
        // Check for failed jobs that need user warning
        const failedJob = jobsData.jobs.find(j => j.status === 'failed' && !j.dismissed);
        if (failedJob) {
          setBannerAlert(failedJob);
        } else {
          setBannerAlert(null);
        }
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Could not connect to API backend.');
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Auth Handler
  const handleAuthSuccess = (newToken, user) => {
    localStorage.setItem('healthpulse_token', newToken);
    setToken(newToken);
    setCurrentUser(user);
    setAuthModalOpen(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('healthpulse_token');
    setToken('');
    setCurrentUser(null);
    setEntries([]);
    setStats(null);
    setGoals(null);
  };

  useEffect(() => {
    if (token) {
      fetchUserProfile(token);
      fetchData();
    } else {
      setLoading(false);
    }
  }, [token, fetchUserProfile, fetchData]);

  // Poll for background scale processing jobs
  useEffect(() => {
    if (!token) return;
    const hasProcessing = activeJobs.some(j => j.status === 'processing');
    if (!hasProcessing) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/upload-scale-photo/status', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (data.success && data.jobs) {
          setActiveJobs(data.jobs);

          // Check if any job completed
          const justCompleted = data.jobs.find(j => j.status === 'completed');
          if (justCompleted) {
            setSuccessToast(`🎉 Successfully parsed ${justCompleted.weight} ${justCompleted.unit || 'lbs'} with Gemini Flash!`);
            setTimeout(() => setSuccessToast(''), 6000);
            fetchData();
          }

          // Check if any job failed
          const failed = data.jobs.find(j => j.status === 'failed' && !j.dismissed);
          if (failed) {
            setBannerAlert(failed);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [token, activeJobs, fetchData]);

  // Dismiss Warning Banner
  const handleDismissBanner = async (jobId) => {
    setBannerAlert(null);
    if (!jobId || !token) return;
    try {
      await fetch(`/api/upload-scale-photo/jobs/${jobId}/dismiss`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (e) {
      console.error(e);
    }
  };

  // Entry CRUD Operations
  const handleSaveEntry = async (entryData) => {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };

    if (editingEntry && editingEntry.id) {
      const res = await fetch(`/api/entries/${editingEntry.id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(entryData)
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || 'Failed to update entry');
    } else {
      const res = await fetch('/api/entries', {
        method: 'POST',
        headers,
        body: JSON.stringify(entryData)
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || 'Failed to create entry');
    }
    setEditingEntry(null);
    await fetchData();
  };

  const handleDeleteEntry = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this entry?')) return;
    try {
      const res = await fetch(`/api/entries/${entryId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error || 'Failed to delete');
      await fetchData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSaveGoals = async (goalsData) => {
    const res = await fetch('/api/goals', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(goalsData)
    });
    const data = await res.json();
    if (!data.success) throw new Error(data.error || 'Failed to save goals');
    await fetchData();
  };

  const isProcessingPhoto = activeJobs.some(j => j.status === 'processing');

  // If not logged in, render the Auth Welcome Screen
  if (!token && !loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-main)' }}>
        <header className="header">
          <div className="container header-container">
            <div className="logo-section">
              <div className="logo-icon">
                <Activity size={24} />
              </div>
              <div>
                <h1 className="logo-title">HealthPulse</h1>
                <p className="logo-subtitle">Secure Multi-User Weight & Activity Tracker</p>
              </div>
            </div>
            <button className="btn btn-primary" onClick={() => setAuthModalOpen(true)}>
              <LogIn size={16} /> Sign In / Register
            </button>
          </div>
        </header>

        <main className="container" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 20px' }}>
          <div style={{
            maxWidth: '480px',
            width: '100%',
            background: 'var(--bg-card)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-medium)',
            padding: '36px',
            textAlign: 'center',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.05)'
          }}>
            <div style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              background: 'var(--brand-primary-subtle)',
              color: 'var(--brand-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 20px'
            }}>
              <ShieldCheck size={32} />
            </div>

            <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--text-primary)', marginBottom: '10px' }}>
              Welcome to HealthPulse
            </h2>

            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: 1.6, marginBottom: '24px' }}>
              Sign in with your password or one-touch <strong>Biometrics (Face ID / Touch ID)</strong> to securely track your weight and daily steps.
            </p>

            <button
              className="btn btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '15px', justifyContent: 'center', marginBottom: '12px' }}
              onClick={() => setAuthModalOpen(true)}
            >
              <LogIn size={18} /> Sign In or Create Account
            </button>
          </div>
        </main>

        <AuthModal
          isOpen={authModalOpen}
          onClose={() => setAuthModalOpen(false)}
          onAuthSuccess={handleAuthSuccess}
        />
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Header */}
      <header className="header">
        <div className="container header-container">
          <div className="logo-section">
            <div className="logo-icon">
              <Activity size={24} />
            </div>
            <div>
              <h1 className="logo-title">HealthPulse</h1>
              <p className="logo-subtitle">Weight & Activity Dashboard</p>
            </div>
          </div>

          <div className="header-actions">
            {isProcessingPhoto && (
              <div className="badge" style={{ background: 'var(--brand-purple-subtle)', color: 'var(--brand-purple)', border: '1px solid var(--brand-purple-border)', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={13} className="animate-spin" />
                Gemini Flash Analyzing Photo...
              </div>
            )}

            <button className="btn btn-secondary" onClick={() => setPhotoModalOpen(true)}>
              <Camera size={16} style={{ color: 'var(--brand-purple)' }} />
              Scan Scale Photo
            </button>

            <button
              className="btn btn-primary"
              onClick={() => { setEditingEntry(null); setEntryModalOpen(true); }}
            >
              <Plus size={16} />
              Log Entry
            </button>

            <button
              className="btn btn-secondary"
              onClick={() => setGoalModalOpen(true)}
              title="Account & Goals"
            >
              <Settings size={16} />
              <span>{currentUser?.username || 'Goals'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="container" style={{ flex: 1, paddingBottom: '60px' }}>
        {/* Success Toast */}
        {successToast && (
          <div style={{
            background: 'rgba(5, 150, 105, 0.1)',
            border: '1px solid rgba(5, 150, 105, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '12px 18px',
            marginTop: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            color: 'var(--brand-primary)',
            fontWeight: 600,
            fontSize: '14px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CheckCircle2 size={18} />
              <span>{successToast}</span>
            </div>
            <button onClick={() => setSuccessToast('')} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--brand-primary)' }}>
              <X size={16} />
            </button>
          </div>
        )}

        {/* Scale Photo Warning Alert Banner */}
        {bannerAlert && (
          <div style={{
            background: 'rgba(217, 119, 6, 0.08)',
            border: '1px solid rgba(217, 119, 6, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: '16px 20px',
            marginTop: '20px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '14px'
          }}>
            <AlertTriangle size={22} style={{ color: 'var(--brand-amber)', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 800, fontSize: '14px', color: 'var(--text-primary)', marginBottom: '4px' }}>
                Scale Photo Could Not Be Read
              </div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {bannerAlert.error || 'The numbers on the scale display were not legible or blurred.'} Your most recent valid entry <strong>({stats?.latest_weight ? `${stats.latest_weight} ${stats?.weight_unit || 'lbs'}` : 'recorded entry'})</strong> is currently displayed on your dashboard.
              </div>
              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => { setPhotoModalOpen(true); handleDismissBanner(bannerAlert.id); }}
                >
                  <Camera size={13} /> Re-upload Scale Photo
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleDismissBanner(bannerAlert.id)}
                >
                  Dismiss Warning
                </button>
              </div>
            </div>
            <button
              onClick={() => handleDismissBanner(bannerAlert.id)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
            >
              <X size={16} />
            </button>
          </div>
        )}

        {/* Metrics Grid */}
        <section style={{ marginTop: '24px' }}>
          <MetricCards stats={stats} goals={goals} />
        </section>

        {/* Charts Grid */}
        <section style={{ marginTop: '24px' }}>
          <Charts entries={entries} goals={goals} />
        </section>

        {/* History Table */}
        <section style={{ marginTop: '24px' }}>
          <HistoryTable
            entries={entries}
            goals={goals}
            onEditEntry={(entry) => { setEditingEntry(entry); setEntryModalOpen(true); }}
            onDeleteEntry={handleDeleteEntry}
          />
        </section>
      </main>

      {/* Modals */}
      <EntryForm
        isOpen={entryModalOpen}
        onClose={() => { setEntryModalOpen(false); setEditingEntry(null); }}
        onSave={handleSaveEntry}
        initialData={editingEntry}
        defaultUnit={goals?.weight_unit || 'lbs'}
      />

      <GoalSettings
        isOpen={goalModalOpen}
        onClose={() => setGoalModalOpen(false)}
        goals={goals}
        onSaveGoals={handleSaveGoals}
        user={currentUser}
        token={token}
        onLogout={handleLogout}
        onPasskeysChanged={() => fetchUserProfile(token)}
      />

      <PhotoUploadModal
        isOpen={photoModalOpen}
        onClose={() => setPhotoModalOpen(false)}
        token={token}
        onUploadStarted={() => {
          fetchData();
        }}
      />

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </div>
  );
}
