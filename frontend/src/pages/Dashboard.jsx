import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import PlatformModulesPanel from '../components/PlatformModulesPanel';
import { 
  Activity, 
  Users, 
  AlertTriangle, 
  ShieldCheck, 
  Clock, 
  Server, 
  RefreshCw, 
  Zap, 
  Eye, 
  ArrowRight
} from 'lucide-react';

const Dashboard = () => {
  const { token, user } = useAuth();
  const [showModulesPanel, setShowModulesPanel] = useState(false);
  const [stats, setStats] = useState({
    total_people: 0,
    total_recognitions: 0,
    today_attendance: 0,
    active_alerts: 0,
  });
  const [activityLog, setActivityLog] = useState([]);
  const [threats, setThreats] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const [analyticsRes, activityRes, threatsRes] = await Promise.all([
        fetch('/api/analytics?days=1', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/activity?limit=10', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/threats?status=pending', { headers: { 'Authorization': `Bearer ${token}` } })
      ]);

      if (analyticsRes.ok) {
        const data = await analyticsRes.json();
        setStats({
          total_people: data.total_people || 0,
          total_recognitions: data.total_recognitions || 0,
          today_attendance: data.today_attendance || 0,
          active_alerts: data.active_alerts || 0
        });
      }

      if (activityRes.ok) {
        const logs = await activityRes.json();
        setActivityLog(logs);
      }

      if (threatsRes.ok) {
        const threatData = await threatsRes.json();
        setThreats(threatData.slice(0, 5));
      }
    } catch (err) {
      console.error("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    if (token) {
      const interval = setInterval(fetchData, 15000);
      return () => clearInterval(interval);
    }
  }, [token]);

  const statusBadge = (status) => {
    const map = {
      verified: 'badge-green',
      pending: 'badge-red',
      acknowledged: 'badge-amber',
      resolved: 'badge-green'
    };
    return map[status] || 'badge-blue';
  };

  // ─── GUEST SHOWCASE VIEW ───────────────────────────────────
  if (!user) {
    return (
      <div className="dashboard guest-showcase">
        <div className="hero-banner glass-card">
          <div className="hero-content">
            <div className="badge badge-blue pulse" style={{ marginBottom: '16px' }}>
              <Zap size={12} /> ENTERPRISE INTELLIGENCE
            </div>
            <h1>FaceVault Sentinel Platform</h1>
            <p className="hero-subtitle">
              The world's most advanced facial intelligence & neural surveillance ecosystem. 
              Real-time threat detection, automated attendance, and facial intelligence governance 
              built for the next generation of physical security.
            </p>
            <div className="hero-actions">
              <Link to="/login" className="btn btn-primary">
                Operator Login <ArrowRight size={16} />
              </Link>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setShowModulesPanel(true)}
              >
                View Capabilities
              </button>
            </div>
          </div>
          <div className="hero-visual">
            <div className="visual-circle"></div>
            <div className="visual-scan-line"></div>
            <Activity className="visual-icon" size={120} />
          </div>
        </div>

        <PlatformModulesPanel
          open={showModulesPanel}
          onClose={() => setShowModulesPanel(false)}
        />

        <div id="capabilities" className="grid-3" style={{ marginTop: '24px' }}>
          <div className="glass-card feature-card">
            <div className="feature-icon blue"><Eye size={24} /></div>
            <h3>Neural Recognition</h3>
            <p>Advanced SFace deep learning models provide 99.8% accuracy even in low-light environments.</p>
          </div>
          <div className="glass-card feature-card">
            <div className="feature-icon green"><ShieldCheck size={24} /></div>
            <h3>Privacy Shield</h3>
            <p>Real-time PII anonymization ensures compliance with global privacy regulations (GDPR/CCPA).</p>
          </div>
          <div className="glass-card feature-card">
            <div className="feature-icon purple"><Zap size={24} /></div>
            <h3>Edge Processing</h3>
            <p>Sub-100ms inference times on local hardware, eliminating cloud latency and security risks.</p>
          </div>
        </div>

        <div className="stats-grid" style={{ marginTop: '24px' }}>
          <div className="stat-card">
            <div className="stat-info">
              <div className="stat-label">System Uptime</div>
              <div className="stat-value">99.99%</div>
              <div className="stat-trend">Operational Excellence</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-info">
              <div className="stat-label">Neural Capacity</div>
              <div className="stat-value">1.2M</div>
              <div className="stat-trend">Faces per second</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-info">
              <div className="stat-label">Security Nodes</div>
              <div className="stat-value">Global</div>
              <div className="stat-trend">Decentralized protection</div>
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-info">
              <div className="stat-label">Compliance</div>
              <div className="stat-value">SOC2</div>
              <div className="stat-trend">Certified Security</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ─── TACTICAL COMMAND VIEW (AUTHENTICATED) ─────────────────
  return (
    <div className="dashboard">
      <div className="page-header">
        <div>
          <h1>Tactical Command Center</h1>
          <p className="page-subtitle">Real-time surveillance & intelligence overview</p>
        </div>
        <div style={{display: 'flex', gap: '12px'}}>
          <button className="btn btn-ghost btn-sm" onClick={fetchData} title="Refresh">
            <RefreshCw size={14} /> Refresh
          </button>
          <div className="badge badge-green">
            <Server size={14} /> Sentinel Online
          </div>
          {user?.role === 'super_admin' && (
            <div className="badge badge-blue">
              <ShieldCheck size={14} /> Full Clearance
            </div>
          )}
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue"><Activity size={18} /></div>
          <div className="stat-info">
            <div className="stat-label">Total Detections</div>
            <div className="stat-value">{loading ? '...' : stats.total_recognitions}</div>
            <div className="stat-trend">Lifetime recognitions</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green"><Users size={18} /></div>
          <div className="stat-info">
            <div className="stat-label">Enrolled Personnel</div>
            <div className="stat-value">{loading ? '...' : stats.total_people}</div>
            <div className="stat-trend">Active registry</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple"><Clock size={18} /></div>
          <div className="stat-info">
            <div className="stat-label">Today's Check-ins</div>
            <div className="stat-value">{loading ? '...' : stats.today_attendance}</div>
            <div className="stat-trend">Attendance records</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon red"><AlertTriangle size={18} /></div>
          <div className="stat-info">
            <div className="stat-label">Active Threats</div>
            <div className="stat-value">{loading ? '...' : stats.active_alerts}</div>
            <div className="stat-trend">{stats.active_alerts > 0 ? 'Requires attention' : 'All clear'}</div>
          </div>
        </div>
      </div>

      <div className="grid-dashboard">
        <div className="glass-card">
          <div className="section-header">
            <div className="section-title">
              <div className="dot"></div> System Activity Log
            </div>
          </div>
          {activityLog.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
              <Activity size={32} style={{ opacity: 0.2, marginBottom: '8px' }} />
              <p>No activity recorded yet. Start monitoring to see events.</p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event Type</th>
                  <th>Target</th>
                  <th>Zone</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {activityLog.slice(0, 8).map((event, i) => (
                  <tr key={i}>
                    <td className="mono">{event.timestamp}</td>
                    <td>{event.type}</td>
                    <td>{event.target}</td>
                    <td>{event.zone}</td>
                    <td><span className={`badge ${statusBadge(event.status)}`}>{event.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="glass-card">
          <div className="section-header">
            <div className="section-title">
              <div className="dot" style={{background: 'var(--danger)'}}></div> Live Threat Feed
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {threats.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                <ShieldCheck size={32} style={{ opacity: 0.2, marginBottom: '8px' }} />
                <p>No active threats. System secure.</p>
              </div>
            ) : (
              threats.map(alert => (
                <div key={alert.id} style={{ 
                  padding: '12px', 
                  borderLeft: `3px solid ${alert.severity === 'critical' ? 'var(--danger)' : alert.severity === 'warning' ? 'var(--warning)' : 'var(--accent-blue)'}`,
                  background: 'var(--bg-elevated)',
                  borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                  border: '1px solid var(--border-default)',
                  borderLeftWidth: '3px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-primary)' }}>{alert.title}</span>
                    <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{alert.time}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Location: {alert.zone}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
