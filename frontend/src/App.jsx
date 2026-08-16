import React, { useState, useEffect, useCallback } from 'react';
import { Activity, Plus, Settings2, RefreshCw, Camera, Sparkles } from 'lucide-react';
import MetricCards from './components/MetricCards';
import Charts from './components/Charts';
import HistoryTable from './components/HistoryTable';
import EntryForm from './components/EntryForm';
import GoalSettings from './components/GoalSettings';
import PhotoUploadModal from './components/PhotoUploadModal';

const API_BASE = '/api';

export default function App() {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [goals, setGoals] = useState({ daily_steps_goal: 10000, target_weight: 165.0, starting_weight: 185.0, weight_unit: 'lbs' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [isGoalsModalOpen, setIsGoalsModalOpen] = useState(false);
  const [isPhotoModalOpen, setIsPhotoModalOpen] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [entriesRes, statsRes, goalsRes] = await Promise.all([
        fetch(`${API_BASE}/entries`),
        fetch(`${API_BASE}/stats`),
        fetch(`${API_BASE}/goals`)
      ]);

      const [entriesData, statsData, goalsData] = await Promise.all([
        entriesRes.json(),
        statsRes.json(),
        goalsRes.json()
      ]);

      if (entriesData.success) setEntries(entriesData.entries || []);
      if (statsData.success) setStats(statsData.stats || null);
      if (goalsData.success) setGoals(goalsData.goals || {});
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('Could not connect to the backend server. Please make sure the Flask API is running.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle Save (Create or Update)
  const handleSaveEntry = async (entryData) => {
    let res;
    if (entryData.id) {
      res = await fetch(`${API_BASE}/entries/${entryData.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entryData)
      });
    } else {
      res = await fetch(`${API_BASE}/entries`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entryData)
      });
    }

    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to save');
    }

    await fetchData();
  };

  // Handle Delete
  const handleDeleteEntry = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/entries/${id}`, { method: 'DELETE' });
      const data = await res.json();
      if (data.success) {
        await fetchData();
      } else {
        alert(data.error || 'Failed to delete');
      }
    } catch (err) {
      alert('Error deleting entry: ' + err.message);
    }
  };

  // Handle Update Goals
  const handleSaveGoals = async (newGoals) => {
    const res = await fetch(`${API_BASE}/goals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newGoals)
    });
    const data = await res.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to update goals');
    }
    await fetchData();
  };

  const handleOpenEdit = (entry) => {
    setEditingEntry(entry);
    setIsLogModalOpen(true);
  };

  const handleOpenNew = () => {
    setEditingEntry(null);
    setIsLogModalOpen(true);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="brand">
          <div className="brand-icon">
            <Activity size={24} />
          </div>
          <div className="brand-text">
            <h1>HealthPulse</h1>
            <p>Daily Weight & Steps Tracker</p>
          </div>
        </div>

        <div className="header-actions">
          <button 
            className="btn btn-secondary" 
            onClick={fetchData} 
            title="Refresh Data"
            disabled={loading}
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
          
          <button 
            className="btn btn-secondary" 
            onClick={() => setIsGoalsModalOpen(true)}
          >
            <Settings2 size={16} />
            Goals
          </button>

          {/* Photo OCR Scan Button */}
          <button 
            className="btn btn-camera" 
            onClick={() => setIsPhotoModalOpen(true)}
            title="Upload photo from bathroom scale"
          >
            <Camera size={16} />
            Scan Scale Photo
          </button>

          {/* Manual Log Button */}
          <button 
            className="btn btn-primary" 
            onClick={handleOpenNew}
          >
            <Plus size={16} />
            Log Entry
          </button>
        </div>
      </header>

      {/* Error alert */}
      {error && (
        <div style={{
          padding: '14px 20px',
          background: 'var(--brand-rose-subtle)',
          border: '1px solid #fecdd3',
          color: 'var(--brand-rose)',
          borderRadius: 'var(--radius-md)',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>{error}</span>
          <button className="btn btn-sm btn-secondary" onClick={fetchData}>Retry</button>
        </div>
      )}

      {/* Metric summary cards */}
      <MetricCards 
        stats={stats} 
        goals={goals} 
        onOpenLogModal={handleOpenNew} 
      />

      {/* Interactive Charts */}
      <Charts 
        entries={entries} 
        goals={goals} 
      />

      {/* History and Logs */}
      <HistoryTable
        entries={entries}
        goals={goals}
        onEdit={handleOpenEdit}
        onDelete={handleDeleteEntry}
      />

      {/* Modals */}
      <PhotoUploadModal
        isOpen={isPhotoModalOpen}
        onClose={() => setIsPhotoModalOpen(false)}
        onEntrySaved={fetchData}
        defaultUnit={goals?.weight_unit || 'lbs'}
      />

      <EntryForm
        isOpen={isLogModalOpen}
        onClose={() => {
          setIsLogModalOpen(false);
          setEditingEntry(null);
        }}
        onSave={handleSaveEntry}
        editingEntry={editingEntry}
        unit={goals?.weight_unit || 'lbs'}
      />

      <GoalSettings
        isOpen={isGoalsModalOpen}
        onClose={() => setIsGoalsModalOpen(false)}
        goals={goals}
        onSaveGoals={handleSaveGoals}
      />
    </div>
  );
}
