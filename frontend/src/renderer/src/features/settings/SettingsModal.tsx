/* ═══════════════════════════════════════════════════════════
   SettingsModal Component — Cloud Sync, Autonomous Workflows,
   Task Scheduler, Clipboard History, Wake Word & Global Hotkeys
   ═══════════════════════════════════════════════════════════ */

import React, { useState, useEffect } from 'react';
import api from '@/shared/lib/api';
import { useAuth } from '@/shared/context/AuthContext';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface IntegrationItem {
  provider: string;
  status: string;
  account_email: string;
  account_name: string;
  last_successful_auth: string | null;
  scopes: string[];
  is_expired: boolean;
}

interface ScheduledTaskItem {
  id: string;
  prompt: string;
  next_run: string | null;
  repeat_type: string;
  status: string;
  last_run: string | null;
  last_result: string;
  run_count: number;
}

interface ClipboardItem {
  id: string;
  content: string;
  category: string;
  is_pinned: boolean;
  captured_at: string;
}

interface WorkflowItem {
  id: string;
  name: string;
  description: string;
  workflow_type: string;
  trigger_type: string;
  interval_minutes: number;
  is_active: boolean;
  status: string;
  last_run: string | null;
  last_status: string;
  last_output: string;
  run_count: number;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'sync' | 'workflows' | 'scheduler' | 'clipboard' | 'ai' | 'voice' | 'about'>('workflows');
  const [integrations, setIntegrations] = useState<IntegrationItem[]>([]);
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTaskItem[]>([]);
  const [clipboardEntries, setClipboardEntries] = useState<ClipboardItem[]>([]);
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [clipboardSearch, setClipboardSearch] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [syncStatusMsg, setSyncStatusMsg] = useState<{ [key: string]: string }>({});
  const [workflowStatusMsg, setWorkflowStatusMsg] = useState<{ [key: string]: string }>({});
  const [tokenInput, setTokenInput] = useState('');
  const [showTokenInput, setShowTokenInput] = useState(false);

  void isLoading;

  const [newPrompt, setNewPrompt] = useState('');
  const [newRunAt, setNewRunAt] = useState('in 1 hour');
  const [newRepeat, setNewRepeat] = useState('once');

  const [alwaysOnTop, setAlwaysOnTop] = useState(false);
  const [autoLaunch, setAutoLaunch] = useState(false);
  const [wakeWordEnabled, setWakeWordEnabled] = useState(true);
  const [copiedClipId, setCopiedClipId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadIntegrations();
      loadScheduledTasks();
      loadClipboardEntries();
      loadWorkflows();
      loadBackgroundSettings();
      loadWakeWordStatus();
    }
  }, [isOpen]);

  const loadBackgroundSettings = async () => {
    if ((window as any).api && (window as any).api.app) {
      try {
        const bgStatus = await (window as any).api.app.getBackgroundStatus();
        setAlwaysOnTop(bgStatus.alwaysOnTop);
        setAutoLaunch(bgStatus.autoLaunch);
        if (typeof bgStatus.wakeWordActive === 'boolean') {
          setWakeWordEnabled(bgStatus.wakeWordActive);
        }
      } catch (e) {
        console.warn('Could not read background settings:', e);
      }
    }
  };

  const loadWakeWordStatus = async () => {
    try {
      const res = await api.get<{ enabled: boolean }>('/voice/wakeword/');
      if (res && typeof res.enabled === 'boolean') {
        setWakeWordEnabled(res.enabled);
      }
    } catch (e) {
      console.warn('Failed to load wake word status:', e);
    }
  };

  const handleToggleWakeWord = async () => {
    const nextState = !wakeWordEnabled;
    setWakeWordEnabled(nextState);
    try {
      await api.post('/voice/wakeword/', { enabled: nextState });
      if ((window as any).api && (window as any).api.app && (window as any).api.app.toggleWakeWord) {
        await (window as any).api.app.toggleWakeWord(nextState);
      }
    } catch (e) {
      console.warn('Failed to update wake word status:', e);
    }
  };

  const handleToggleAlwaysOnTop = async () => {
    if ((window as any).api && (window as any).api.app) {
      try {
        const val = await (window as any).api.app.toggleAlwaysOnTop();
        setAlwaysOnTop(val);
      } catch (e) {
        console.warn('Toggle always-on-top failed:', e);
      }
    }
  };

  const handleToggleAutoLaunch = async () => {
    if ((window as any).api && (window as any).api.app) {
      try {
        const nextVal = !autoLaunch;
        const val = await (window as any).api.app.setAutoLaunch(nextVal);
        setAutoLaunch(val);
      } catch (e) {
        console.warn('Toggle auto-launch failed:', e);
      }
    }
  };

  const handleToggleFloatingWidget = async () => {
    if ((window as any).api && (window as any).api.app && (window as any).api.app.toggleWidget) {
      try {
        await (window as any).api.app.toggleWidget();
      } catch (e) {
        console.warn('Toggle widget failed:', e);
      }
    }
  };

  const loadWorkflows = async () => {
    try {
      const res = await api.get<{ workflows: WorkflowItem[] }>('/workflows/');
      if (res && res.workflows) {
        setWorkflows(res.workflows);
      }
    } catch (e) {
      console.warn('Failed to load workflows:', e);
    }
  };

  const handleToggleWorkflow = async (wf: WorkflowItem) => {
    try {
      const nextActive = !wf.is_active;
      await api.post(`/workflows/${wf.id}/`, { is_active: nextActive });
      setWorkflows((prev) =>
        prev.map((w) => (w.id === wf.id ? { ...w, is_active: nextActive } : w))
      );
    } catch (e) {
      console.warn('Failed to toggle workflow:', e);
    }
  };

  const handleTriggerWorkflow = async (wfId: string) => {
    setWorkflowStatusMsg((prev) => ({ ...prev, [wfId]: '⏳ Executing background loop...' }));
    try {
      const res = await api.post<{ success: boolean; result: string }>(`/workflows/${wfId}/trigger/`, {});
      setWorkflowStatusMsg((prev) => ({
        ...prev,
        [wfId]: res.success ? `✅ Complete: ${res.result.slice(0, 80)}...` : `❌ Error: ${res.result}`
      }));
      loadWorkflows();
    } catch (e: any) {
      setWorkflowStatusMsg((prev) => ({ ...prev, [wfId]: `❌ Execution failed: ${e?.message || 'Error'}` }));
    }
  };

  const loadIntegrations = async () => {
    try {
      const res = await api.get<{ integrations: IntegrationItem[] }>('/integrations/');
      if (res && res.integrations) {
        setIntegrations(res.integrations);
      }
    } catch (e) {
      console.warn('Failed to load integrations:', e);
    }
  };

  const loadScheduledTasks = async () => {
    try {
      const res = await api.get<{ scheduled_tasks: ScheduledTaskItem[] }>('/scheduler/');
      if (res && res.scheduled_tasks) {
        setScheduledTasks(res.scheduled_tasks);
      }
    } catch (e) {
      console.warn('Failed to load scheduled tasks:', e);
    }
  };

  const loadClipboardEntries = async () => {
    try {
      const res = await api.get<{ clipboard_entries: ClipboardItem[] }>('/clipboard/');
      if (res && res.clipboard_entries) {
        setClipboardEntries(res.clipboard_entries);
      }
    } catch (e) {
      console.warn('Failed to load clipboard entries:', e);
    }
  };

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPrompt.trim()) return;
    try {
      await api.post('/scheduler/', {
        prompt: newPrompt.trim(),
        run_at: newRunAt.trim(),
        repeat: newRepeat
      });
      setNewPrompt('');
      loadScheduledTasks();
    } catch (err) {
      console.warn('Failed to create scheduled task:', err);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await api.delete(`/scheduler/${taskId}/`);
      loadScheduledTasks();
    } catch (err) {
      console.warn('Failed to cancel task:', err);
    }
  };

  const handleCopyClipboardEntry = (entry: ClipboardItem) => {
    navigator.clipboard.writeText(entry.content);
    setCopiedClipId(entry.id);
    setTimeout(() => setCopiedClipId(null), 2000);
  };

  const handleTestSync = async (provider: string) => {
    setSyncStatusMsg((prev) => ({ ...prev, [provider]: 'Testing real-time sync...' }));
    try {
      const res = await api.post<{ status: string; synced: boolean; message: string }>(
        `/integrations/${provider}/sync/`,
        {}
      );
      setSyncStatusMsg((prev) => ({
        ...prev,
        [provider]: res.synced ? `✅ ${res.message}` : `⚠️ ${res.message}`
      }));
      loadIntegrations();
    } catch (e: any) {
      setSyncStatusMsg((prev) => ({
        ...prev,
        [provider]: `❌ Sync Error: ${e?.message || 'Connection failed'}`
      }));
    }
  };

  const handleConnect = async (provider: string) => {
    window.location.href = `http://127.0.0.1:8000/api/auth/${provider}/login/`;
  };

  const handleDisconnect = async (provider: string) => {
    setIsLoading(true);
    try {
      await api.post(`/integrations/${provider}/disconnect/`, {});
      setSyncStatusMsg((prev) => ({ ...prev, [provider]: `Disconnected ${provider}.` }));
      loadIntegrations();
    } catch (e: any) {
      setSyncStatusMsg((prev) => ({ ...prev, [provider]: `Failed to disconnect: ${e?.message || 'Error'}` }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleManualTokenSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tokenInput.trim()) return;
    setIsLoading(true);
    try {
      await api.post('/integrations/google/link-token/', {
        access_token: tokenInput.trim(),
        account_email: user?.email || 'user@google.com'
      });
      setSyncStatusMsg((prev) => ({ ...prev, google: '✅ Google OAuth token linked to AES-256-GCM vault successfully!' }));
      setTokenInput('');
      setShowTokenInput(false);
      loadIntegrations();
    } catch (e: any) {
      setSyncStatusMsg((prev) => ({ ...prev, google: `❌ Token link failed: ${e?.message || 'Error'}` }));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const googleInteg = integrations.find((i) => i.provider === 'google');

  const filteredClipboard = clipboardEntries.filter((c) =>
    c.content.toLowerCase().includes(clipboardSearch.toLowerCase()) ||
    c.category.toLowerCase().includes(clipboardSearch.toLowerCase())
  );

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(5, 8, 16, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        animation: 'var(--animate-fade-in)'
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '880px',
          maxWidth: '95vw',
          height: '680px',
          maxHeight: '94vh',
          background: '#0F172A',
          border: '1px solid #334155',
          borderRadius: '16px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '18px 24px',
            borderBottom: '1px solid #1E293B',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#0B1120'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: '8px',
                background: 'rgba(139, 92, 246, 0.15)',
                border: '1px solid #8B5CF6',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#A78BFA',
                fontSize: '1.1rem'
              }}
            >
              ⚡
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 700, color: '#F8FAFC' }}>
                Control Center & Background AI
              </h2>
              <p style={{ margin: 0, fontSize: '0.75rem', color: '#94A3B8' }}>
                Autonomous workflows, wake word detection, global hotkeys, and cloud vault
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#94A3B8',
              fontSize: '1.25rem',
              cursor: 'pointer',
              padding: '6px 10px',
              borderRadius: '6px'
            }}
          >
            ✕
          </button>
        </div>

        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          {/* Sidebar Tabs */}
          <div
            style={{
              width: '220px',
              borderRight: '1px solid #1E293B',
              padding: '16px 12px',
              display: 'flex',
              flexDirection: 'column',
              gap: 6,
              background: '#0B1120'
            }}
          >
            <button
              onClick={() => setActiveTab('workflows')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'workflows' ? '#1E293B' : 'transparent',
                color: activeTab === 'workflows' ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === 'workflows' ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              🤖 Workflows & Loops
            </button>
            <button
              onClick={() => setActiveTab('sync')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'sync' ? '#1E293B' : 'transparent',
                color: activeTab === 'sync' ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === 'sync' ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              ☁️ Cloud Sync
            </button>
            <button
              onClick={() => setActiveTab('scheduler')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'scheduler' ? '#1E293B' : 'transparent',
                color: activeTab === 'scheduler' ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === 'scheduler' ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              ⏰ Task Scheduler
            </button>
            <button
              onClick={() => setActiveTab('clipboard')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'clipboard' ? '#1E293B' : 'transparent',
                color: activeTab === 'clipboard' ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === 'clipboard' ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              📋 Clipboard History
            </button>
            <button
              onClick={() => setActiveTab('voice')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'voice' ? '#1E293B' : 'transparent',
                color: activeTab === 'voice' ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === 'voice' ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              🎙️ Wake Word & Voice
            </button>
            <button
              onClick={() => setActiveTab('ai')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'ai' ? '#1E293B' : 'transparent',
                color: activeTab === 'ai' ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === 'ai' ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              🏝️ Dynamic Island & AI
            </button>
            <button
              onClick={() => setActiveTab('about')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'about' ? '#1E293B' : 'transparent',
                color: activeTab === 'about' ? '#38BDF8' : '#94A3B8',
                fontWeight: activeTab === 'about' ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              ℹ️ Global Shortcuts
            </button>
          </div>

          {/* Main Content Body */}
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
            {/* WORKFLOWS TAB */}
            {activeTab === 'workflows' && (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <h3 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#F8FAFC' }}>
                    🤖 Autonomous Background Workflows & Loops
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: '#94A3B8' }}>
                    Persistent background agents that execute routines, manage system health, and clean files.
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {workflows.map((wf) => (
                    <div
                      key={wf.id}
                      style={{
                        background: '#1E293B',
                        padding: '16px',
                        borderRadius: '10px',
                        border: '1px solid #334155',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 10
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span style={{ fontSize: '1.2rem' }}>{wf.is_active ? '🟢' : '⚪'}</span>
                          <div>
                            <div style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.9375rem' }}>
                              {wf.name}
                            </div>
                            <div style={{ color: '#94A3B8', fontSize: '0.75rem', marginTop: 2 }}>
                              Interval: Every {wf.interval_minutes} mins · Run count: {wf.run_count} · Status: {wf.status}
                            </div>
                          </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <button
                            onClick={() => handleTriggerWorkflow(wf.id)}
                            style={{
                              background: 'rgba(56, 189, 248, 0.15)',
                              color: '#38BDF8',
                              border: '1px solid rgba(56, 189, 248, 0.4)',
                              borderRadius: '6px',
                              padding: '5px 12px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              cursor: 'pointer'
                            }}
                          >
                            ⚡ Run Now
                          </button>
                          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                            <input
                              type="checkbox"
                              checked={wf.is_active}
                              onChange={() => handleToggleWorkflow(wf)}
                              style={{ width: 18, height: 18, cursor: 'pointer' }}
                            />
                            <span style={{ fontSize: '0.75rem', color: wf.is_active ? '#4ADE80' : '#94A3B8' }}>
                              {wf.is_active ? 'Active' : 'Paused'}
                            </span>
                          </label>
                        </div>
                      </div>

                      <p style={{ margin: 0, fontSize: '0.8125rem', color: '#CBD5E1', lineHeight: 1.4 }}>
                        {wf.description}
                      </p>

                      {workflowStatusMsg[wf.id] && (
                        <div style={{ fontSize: '0.75rem', color: '#38BDF8', background: 'rgba(0,0,0,0.3)', padding: '6px 10px', borderRadius: '6px' }}>
                          {workflowStatusMsg[wf.id]}
                        </div>
                      )}

                      {wf.last_run && (
                        <div style={{ fontSize: '0.7rem', color: '#64748B' }}>
                          Last executed: {new Date(wf.last_run).toLocaleString()} ({wf.last_status})
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* CLOUD SYNC TAB */}
            {activeTab === 'sync' && (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <h3 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#F8FAFC' }}>
                    OAuth2 Cloud Integrations & Encrypted Vault
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: '#94A3B8' }}>
                    Connect external accounts. Refresh tokens are secured in an AES-256-GCM encrypted vault.
                  </p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <div style={{ background: '#1E293B', padding: '16px', borderRadius: '10px', border: '1px solid #334155' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ fontSize: '1.5rem' }}>🔴</span>
                        <div>
                          <div style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.9375rem' }}>Google Workspace</div>
                          <div style={{ color: '#94A3B8', fontSize: '0.75rem' }}>
                            {googleInteg?.status === 'CONNECTED'
                              ? `Connected as ${googleInteg.account_email || 'Authorized'}`
                              : 'Connect Gmail, Calendar, Docs & Drive'}
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: 8 }}>
                        {googleInteg?.status === 'CONNECTED' ? (
                          <>
                            <button
                              onClick={() => handleTestSync('google')}
                              style={{ background: '#0F172A', color: '#38BDF8', border: '1px solid #38BDF8', padding: '6px 12px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                            >
                              Sync Now
                            </button>
                            <button
                              onClick={() => handleDisconnect('google')}
                              style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#F87171', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '6px 12px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                            >
                              Disconnect
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={() => handleConnect('google')}
                            style={{ background: '#38BDF8', color: '#0F172A', border: 'none', padding: '6px 14px', borderRadius: '6px', fontWeight: 600, fontSize: '0.75rem', cursor: 'pointer' }}
                          >
                            Connect Google
                          </button>
                        )}
                      </div>
                    </div>
                    {syncStatusMsg['google'] && (
                      <p style={{ margin: '10px 0 0 0', fontSize: '0.75rem', color: '#94A3B8' }}>{syncStatusMsg['google']}</p>
                    )}
                  </div>

                  <div style={{ background: '#1E293B', padding: '14px 16px', borderRadius: '10px', border: '1px solid #334155' }}>
                    <button
                      onClick={() => setShowTokenInput(!showTokenInput)}
                      style={{ background: 'none', border: 'none', color: '#94A3B8', fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
                    >
                      <span>🔑 Direct Google OAuth Token Link (Vault Injection)</span>
                    </button>
                    {showTokenInput && (
                      <form onSubmit={handleManualTokenSubmit} style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                        <input
                          type="password"
                          placeholder="Paste ya29.* Google Access Token"
                          value={tokenInput}
                          onChange={(e) => setTokenInput(e.target.value)}
                          style={{ flex: 1, background: '#0F172A', border: '1px solid #475569', color: '#F8FAFC', padding: '6px 10px', borderRadius: '6px', fontSize: '0.8125rem' }}
                        />
                        <button type="submit" style={{ background: '#38BDF8', color: '#0F172A', border: 'none', padding: '6px 14px', borderRadius: '6px', fontWeight: 600, fontSize: '0.8125rem', cursor: 'pointer' }}>
                          Save Token
                        </button>
                      </form>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* SCHEDULER TAB */}
            {activeTab === 'scheduler' && (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <h3 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#F8FAFC' }}>
                    Scheduled Tasks & Automated Jobs
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: '#94A3B8' }}>
                    Manage recurring AI routines, morning briefings, and timed reminders.
                  </p>
                </div>

                <form onSubmit={handleCreateTask} style={{ background: '#1E293B', padding: '14px', borderRadius: '10px', border: '1px solid #334155', marginBottom: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <span style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.8125rem' }}>+ Create Scheduled Job</span>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <input
                      type="text"
                      placeholder="Prompt (e.g. Check system health and send report)"
                      value={newPrompt}
                      onChange={(e) => setNewPrompt(e.target.value)}
                      style={{ flex: 2, background: '#0F172A', border: '1px solid #475569', color: '#F8FAFC', padding: '6px 10px', borderRadius: '6px', fontSize: '0.8125rem' }}
                    />
                    <input
                      type="text"
                      placeholder="Run at (e.g. in 1 hour)"
                      value={newRunAt}
                      onChange={(e) => setNewRunAt(e.target.value)}
                      style={{ flex: 1, background: '#0F172A', border: '1px solid #475569', color: '#F8FAFC', padding: '6px 10px', borderRadius: '6px', fontSize: '0.8125rem' }}
                    />
                    <select
                      value={newRepeat}
                      onChange={(e) => setNewRepeat(e.target.value)}
                      style={{ background: '#0F172A', border: '1px solid #475569', color: '#F8FAFC', padding: '6px 10px', borderRadius: '6px', fontSize: '0.8125rem' }}
                    >
                      <option value="once">Once</option>
                      <option value="hourly">Hourly</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </select>
                    <button type="submit" style={{ background: '#38BDF8', color: '#0F172A', border: 'none', padding: '6px 14px', borderRadius: '6px', fontWeight: 600, fontSize: '0.8125rem', cursor: 'pointer' }}>
                      Schedule
                    </button>
                  </div>
                </form>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {scheduledTasks.length === 0 ? (
                    <div style={{ padding: '24px', textAlign: 'center', color: '#64748B', fontSize: '0.875rem' }}>
                      No scheduled tasks active. You can create one above or ask the AI in chat.
                    </div>
                  ) : (
                    scheduledTasks.map((t) => (
                      <div key={t.id} style={{ background: '#1E293B', padding: '12px 14px', borderRadius: '8px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.875rem' }}>{t.prompt}</span>
                            <span style={{ fontSize: '0.7rem', padding: '1px 6px', borderRadius: '4px', background: '#334155', color: '#38BDF8' }}>{t.repeat_type}</span>
                          </div>
                          <p style={{ margin: '3px 0 0 0', fontSize: '0.75rem', color: '#94A3B8' }}>
                            Next Run: {t.next_run ? new Date(t.next_run).toLocaleString() : 'N/A'} · Status: {t.status}
                          </p>
                        </div>
                        <button
                          onClick={() => handleCancelTask(t.id)}
                          style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#F87171', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', padding: '4px 10px', fontSize: '0.75rem', cursor: 'pointer' }}
                        >
                          Cancel
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* CLIPBOARD TAB */}
            {activeTab === 'clipboard' && (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <h3 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#F8FAFC' }}>
                    Smart Clipboard History
                  </h3>
                  <p style={{ margin: 0, fontSize: '0.8125rem', color: '#94A3B8' }}>
                    Background monitor automatically indexes copied links, code, and text.
                  </p>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <input
                    type="text"
                    placeholder="Search clipboard snippets (links, code, text)..."
                    value={clipboardSearch}
                    onChange={(e) => setClipboardSearch(e.target.value)}
                    style={{ width: '100%', background: '#1E293B', border: '1px solid #334155', color: '#F8FAFC', padding: '8px 12px', borderRadius: '8px', fontSize: '0.8125rem' }}
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {filteredClipboard.length === 0 ? (
                    <div style={{ padding: '24px', textAlign: 'center', color: '#64748B', fontSize: '0.875rem' }}>
                      No clipboard entries found. Copy any text or link on your PC to see it here.
                    </div>
                  ) : (
                    filteredClipboard.map((c) => (
                      <div key={c.id} style={{ background: '#1E293B', padding: '12px 14px', borderRadius: '8px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                            <span style={{ fontSize: '0.75rem', padding: '1px 6px', borderRadius: '4px', background: '#334155', color: '#38BDF8', textTransform: 'uppercase', fontWeight: 600 }}>
                              {c.category}
                            </span>
                            <span style={{ fontSize: '0.7rem', color: '#64748B' }}>
                              {new Date(c.captured_at).toLocaleTimeString()}
                            </span>
                          </div>
                          <p style={{ margin: 0, fontSize: '0.8125rem', color: '#E2E8F0', wordBreak: 'break-all', fontFamily: c.category === 'code' ? 'monospace' : 'inherit' }}>
                            {c.content.length > 200 ? `${c.content.slice(0, 200)}...` : c.content}
                          </p>
                        </div>
                        <button
                          onClick={() => handleCopyClipboardEntry(c)}
                          style={{ background: copiedClipId === c.id ? '#166534' : '#0F172A', color: copiedClipId === c.id ? '#4ADE80' : '#94A3B8', border: '1px solid #334155', borderRadius: '6px', padding: '4px 10px', fontSize: '0.75rem', cursor: 'pointer', flexShrink: 0 }}
                        >
                          {copiedClipId === c.id ? 'Copied!' : 'Copy'}
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* VOICE & WAKE WORD TAB */}
            {activeTab === 'voice' && (
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#F8FAFC' }}>
                  🎙️ Wake Word & Voice Intelligence
                </h3>
                <p style={{ margin: '0 0 20px 0', fontSize: '0.8125rem', color: '#94A3B8' }}>
                  Hands-free acoustic detection & high-accuracy Whisper speech-to-text.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ background: '#1E293B', padding: '16px', borderRadius: '10px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.875rem' }}>
                        🎙️ Wake Word Detection ("Hey Chaitanya")
                      </span>
                      <p style={{ margin: '4px 0 0 0', color: '#94A3B8', fontSize: '0.75rem' }}>
                        Listens in background. Speak <em>"Hey Chaitanya"</em> or <em>"Chaitanya"</em> to trigger the assistant hands-free.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={wakeWordEnabled}
                      onChange={handleToggleWakeWord}
                      style={{ width: 18, height: 18, cursor: 'pointer' }}
                    />
                  </div>

                  <div style={{ background: '#1E293B', padding: '16px', borderRadius: '10px', border: '1px solid #334155' }}>
                    <div style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.875rem', marginBottom: 6 }}>
                      Trigger Phrases
                    </div>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ background: '#0F172A', color: '#38BDF8', padding: '4px 10px', borderRadius: '6px', border: '1px solid #475569', fontSize: '0.8125rem' }}>"Hey Chaitanya"</span>
                      <span style={{ background: '#0F172A', color: '#38BDF8', padding: '4px 10px', borderRadius: '6px', border: '1px solid #475569', fontSize: '0.8125rem' }}>"Chaitanya"</span>
                      <span style={{ background: '#0F172A', color: '#38BDF8', padding: '4px 10px', borderRadius: '6px', border: '1px solid #475569', fontSize: '0.8125rem' }}>"Ok Chaitanya"</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* DYNAMIC ISLAND & AI TAB */}
            {activeTab === 'ai' && (
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#F8FAFC' }}>
                  🏝️ Floating Dynamic Island & Background Mode
                </h3>
                <p style={{ margin: '0 0 20px 0', fontSize: '0.8125rem', color: '#94A3B8' }}>
                  Floating desktop widgets, window behavior, and vision inspection.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                  <div style={{ background: '#1E293B', padding: '16px', borderRadius: '10px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.875rem' }}>
                        🏝️ Floating Dynamic Island Mini Bar
                      </span>
                      <p style={{ margin: '4px 0 0 0', color: '#94A3B8', fontSize: '0.75rem' }}>
                        Shows live CPU/RAM metrics and quick voice/screen buttons at screen top. Shortcut: <kbd style={{ color: '#38BDF8' }}>Ctrl+Shift+W</kbd>.
                      </p>
                    </div>
                    <button
                      onClick={handleToggleFloatingWidget}
                      style={{ background: '#8B5CF6', color: '#FFF', border: 'none', padding: '6px 14px', borderRadius: '6px', fontWeight: 600, fontSize: '0.8125rem', cursor: 'pointer' }}
                    >
                      Toggle Island
                    </button>
                  </div>

                  <div style={{ background: '#1E293B', padding: '16px', borderRadius: '10px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.875rem' }}>
                        📌 Always On Top (Floating Mode)
                      </span>
                      <p style={{ margin: '4px 0 0 0', color: '#94A3B8', fontSize: '0.75rem' }}>
                        Keep assistant window floating above other active applications.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={alwaysOnTop}
                      onChange={handleToggleAlwaysOnTop}
                      style={{ width: 18, height: 18, cursor: 'pointer' }}
                    />
                  </div>

                  <div style={{ background: '#1E293B', padding: '16px', borderRadius: '10px', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ color: '#F8FAFC', fontWeight: 600, fontSize: '0.875rem' }}>
                        🚀 Launch on Windows Boot
                      </span>
                      <p style={{ margin: '4px 0 0 0', color: '#94A3B8', fontSize: '0.75rem' }}>
                        Start minimized in background system tray when your computer starts.
                      </p>
                    </div>
                    <input
                      type="checkbox"
                      checked={autoLaunch}
                      onChange={handleToggleAutoLaunch}
                      style={{ width: 18, height: 18, cursor: 'pointer' }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* ABOUT & SHORTCUTS TAB */}
            {activeTab === 'about' && (
              <div>
                <h3 style={{ margin: '0 0 4px 0', fontSize: '1rem', color: '#F8FAFC' }}>
                  Chaitanya Karya — Global Hotkeys & Diagnostics
                </h3>
                <p style={{ margin: '0 0 20px 0', fontSize: '0.8125rem', color: '#94A3B8' }}>
                  All global background shortcuts available system-wide across all applications.
                </p>
                <div style={{ background: '#1E293B', padding: '16px', borderRadius: '10px', border: '1px solid #334155', display: 'flex', flexDirection: 'column', gap: 12, fontSize: '0.8125rem', color: '#CBD5E1' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Global Summon / Minimize Assistant:</span>
                    <kbd style={{ background: '#0F172A', padding: '3px 10px', borderRadius: '4px', border: '1px solid #475569', color: '#38BDF8' }}>Ctrl + Shift + Space</kbd>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Spotlight Quick Command Overlay:</span>
                    <kbd style={{ background: '#0F172A', padding: '3px 10px', borderRadius: '4px', border: '1px solid #475569', color: '#38BDF8' }}>Ctrl + Shift + K</kbd>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Floating Dynamic Island Mini Bar:</span>
                    <kbd style={{ background: '#0F172A', padding: '3px 10px', borderRadius: '4px', border: '1px solid #475569', color: '#38BDF8' }}>Ctrl + Shift + W</kbd>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Global Text Selection AI Popup:</span>
                    <kbd style={{ background: '#0F172A', padding: '3px 10px', borderRadius: '4px', border: '1px solid #475569', color: '#38BDF8' }}>Ctrl + Shift + E</kbd>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Voice Wake Word Trigger:</span>
                    <span style={{ color: '#4ADE80' }}>"Hey Chaitanya" (Active)</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>Sandboxed & Policy-Verified Tools:</span>
                    <span style={{ color: '#F8FAFC', fontWeight: 600 }}>39 Local, Cloud & Vision Tools</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
