import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  CalendarClock, 
  Download, 
  ChevronLeft, 
  ChevronRight, 
  ScanFace, 
  LogOut, 
  FileSpreadsheet,
  Zap,
  ShieldCheck,
  UserCheck,
  ArrowRight
} from 'lucide-react';

const Attendance = () => {
  const { token, user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    if (token) {
      fetchLogs();
      const interval = setInterval(fetchLogs, 10000);
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [date, token]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/attendance?date_str=${date}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error("Failed to fetch attendance logs", err);
    } finally {
      setLoading(false);
    }
  };

  const changeDate = (days) => {
    const d = new Date(date);
    d.setDate(d.getDate() + days);
    setDate(d.toISOString().split('T')[0]);
  };

  const handleCheckout = async (personName) => {
    try {
      const res = await fetch(`/api/attendance/checkout/${personName}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchLogs();
      }
    } catch (err) {
      console.error("Failed to checkout", err);
    }
  };

  const exportToExcel = async () => {
    try {
      const res = await fetch(`/api/attendance/export?date_str=${date}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `FaceVault_Attendance_${date}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error("Failed to export Excel", err);
    }
  };

  const formatTime = (isoStr) => {
    if (!isoStr) return null;
    try {
      const d = new Date(isoStr);
      if (isNaN(d.getTime())) return isoStr;
      return d.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit', 
        second: '2-digit', 
        hour12: true 
      });
    } catch {
      return isoStr;
    }
  };

  // ─── GUEST PROMO VIEW ──────────────────────────────────────
  if (!user) {
    return (
      <div className="attendance guest-showcase">
        <div className="hero-banner glass-card" style={{ background: 'radial-gradient(circle at top left, rgba(34, 197, 94, 0.1), transparent), var(--bg-surface)' }}>
          <div className="hero-content">
            <div className="badge badge-green pulse" style={{ marginBottom: '16px' }}>
              <Zap size={12} /> SMART WORKFORCE
            </div>
            <h1>Neural Attendance Protocol</h1>
            <p className="hero-subtitle">
              Eliminate friction and identity fraud with FaceVault's automated attendance system. 
              Our neural engine verifies personnel in real-time as they enter, logging 
              clock-in and clock-out events without manual intervention.
            </p>
            <div className="hero-actions">
              <a href="/login" className="btn btn-primary">
                Personnel Login <ArrowRight size={16} />
              </a>
            </div>
          </div>
          <div className="hero-visual">
            <div className="visual-circle" style={{ borderColor: 'var(--success)' }}></div>
            <div className="visual-scan-line" style={{ background: 'linear-gradient(90deg, transparent, var(--success), transparent)' }}></div>
            <UserCheck className="visual-icon" size={120} style={{ color: 'var(--success)', filter: 'drop-shadow(0 0 15px rgba(34, 197, 94, 0.4))' }} />
          </div>
        </div>

        <div className="grid-3" style={{ marginTop: '24px' }}>
          <div className="glass-card feature-card">
            <div className="feature-icon green"><ScanFace size={24} /></div>
            <h3>Zero Contact</h3>
            <p>Verification happens instantly as employees walk past the terminal. No cards, no fingerprints.</p>
          </div>
          <div className="glass-card feature-card">
            <div className="feature-icon blue"><ShieldCheck size={24} /></div>
            <h3>Anti-Spoofing</h3>
            <p>Integrated liveness detection prevents fraud from photos, videos, or 3D masks.</p>
          </div>
          <div className="glass-card feature-card">
            <div className="feature-icon purple"><FileSpreadsheet size={24} /></div>
            <h3>Excel Integration</h3>
            <p>One-click professional reporting for HR and payroll management.</p>
          </div>
        </div>
      </div>
    );
  }

  // ─── OPERATIONAL LOG VIEW (AUTHENTICATED) ──────────────────
  return (
    <div className="attendance">
      <div className="page-header">
        <div>
          <h1>Attendance Logs</h1>
          <p className="page-subtitle">Facial recognition-based check-in verification</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-surface)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-sm)' }}>
            <button className="icon-btn" onClick={() => changeDate(-1)}><ChevronLeft size={16} /></button>
            <span className="mono" style={{ padding: '0 12px', fontSize: '0.85rem' }}>{date}</span>
            <button className="icon-btn" onClick={() => changeDate(1)}><ChevronRight size={16} /></button>
          </div>
          <button className="btn btn-primary" onClick={exportToExcel} disabled={logs.length === 0}>
            <FileSpreadsheet size={16} /> Export Excel
          </button>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-info">
            <div className="stat-label">Total Present</div>
            <div className="stat-value">{logs.length}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-info">
            <div className="stat-label">On Time</div>
            <div className="stat-value" style={{ color: 'var(--success)' }}>
              {logs.filter(l => l.status === 'present').length}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-info">
            <div className="stat-label">Late Arrivals</div>
            <div className="stat-value" style={{ color: 'var(--warning)' }}>
              {logs.filter(l => l.status === 'late').length}
            </div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-info">
            <div className="stat-label">Active Shifts</div>
            <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>
              {logs.filter(l => !l.check_out).length}
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Authentication</th>
              <th>Personnel</th>
              <th>Check-in Time</th>
              <th>Check-out Time</th>
              <th>Match Confidence</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="7" style={{ textAlign: 'center', padding: '32px' }}>Loading logs...</td></tr>
            ) : logs.length === 0 ? (
              <tr><td colSpan="7" style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                <CalendarClock size={32} style={{ opacity: 0.2, display: 'block', margin: '0 auto 12px' }} />
                No records for {date}. Attendance is auto-logged when recognized faces appear on the Live Monitor.
              </td></tr>
            ) : (
              logs.map(log => (
                <tr key={log.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-blue)' }}>
                      <ScanFace size={16} /> 
                      <span style={{ fontSize: '0.75rem', fontWeight: '500' }}>Face Recognition</span>
                    </div>
                  </td>
                  <td style={{ fontWeight: '600' }}>{log.person_name}</td>
                  <td className="mono">{formatTime(log.check_in) || '—'}</td>
                  <td className="mono" style={{ color: log.check_out ? 'inherit' : 'var(--text-muted)' }}>
                    {log.check_out ? formatTime(log.check_out) : 'Active shift'}
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ flex: 1, height: '4px', background: 'var(--bg-elevated)', borderRadius: '2px' }}>
                        <div style={{ 
                          height: '100%', 
                          width: `${log.confidence}%`, 
                          background: log.confidence > 80 ? 'var(--success)' : 'var(--warning)',
                          borderRadius: '2px'
                        }}></div>
                      </div>
                      <span className="mono" style={{ fontSize: '0.75rem' }}>{typeof log.confidence === 'number' ? log.confidence.toFixed(1) : 0}%</span>
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${log.status === 'present' ? 'badge-green' : 'badge-amber'}`}>
                      {log.status.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {!log.check_out && (
                      <button 
                        className="btn btn-ghost btn-sm" 
                        onClick={() => handleCheckout(log.person_name)}
                        title="Check out"
                      >
                        <LogOut size={14} /> Check Out
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Attendance;
