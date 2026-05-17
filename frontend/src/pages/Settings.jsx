import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Settings as SettingsIcon, 
  Shield, 
  Server, 
  Database, 
  Save, 
  HardDrive, 
  RefreshCw,
  Cpu,
  Zap,
  Globe,
  ArrowRight,
  Code
} from 'lucide-react';

const Settings = () => {
  const { token, user } = useAuth();
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSystemInfo = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const res = await fetch('/api/system/info', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setSystemInfo(data);
      }
    } catch (err) {
      console.error("Failed to load system info");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemInfo();
  }, [token]);

  // ─── GUEST SHOWCASE VIEW ───────────────────────────────────
  if (!user) {
    return (
      <div className="settings guest-showcase">
        <div className="hero-banner glass-card hero-accent-purple">
          <div className="hero-content">
            <div className="badge badge-purple pulse" style={{ marginBottom: '16px' }}>
              <Cpu size={12} /> CORE ARCHITECTURE
            </div>
            <h1>System Infrastructure</h1>
            <p className="hero-subtitle">
              FaceVault is engineered on a high-performance ASGI stack, combining the 
              speed of Python's FastAPI with the reactivity of React 18. Our 
              decentralized architecture ensures maximum privacy and uptime.
            </p>
            <div className="hero-actions">
              <Link to="/login" className="btn btn-primary">
                Operator Login <ArrowRight size={16} />
              </Link>
            </div>
          </div>
          <div className="hero-visual">
            <div className="visual-circle" ></div>
            <div className="visual-scan-line" ></div>
            <Server className="visual-icon" size={120}  />
          </div>
        </div>

        <div className="grid-3" style={{ marginTop: '24px' }}>
          <div className="glass-card feature-card">
            <div className="feature-icon purple"><Zap size={24} /></div>
            <h3>Lightning FastAPI</h3>
            <p>Built on the fastest modern Python framework for high-concurrency websocket handling.</p>
          </div>
          <div className="glass-card feature-card">
            <div className="feature-icon blue"><Code size={24} /></div>
            <h3>React 18 Frontend</h3>
            <p>Ultra-responsive concurrent rendering for real-time surveillance visualization.</p>
          </div>
          <div className="glass-card feature-card">
            <div className="feature-icon green"><Database size={24} /></div>
            <h3>Local Sovereignty</h3>
            <p>SQLite storage ensures your facial data never leaves your infrastructure.</p>
          </div>
        </div>
      </div>
    );
  }

  // ─── OPERATIONAL DIAGNOSTICS VIEW (AUTHENTICATED) ──────────
  return (
    <div className="settings">
      <div className="page-header">
        <div>
          <h1>System Configuration</h1>
          <p className="page-subtitle">Super Admin control panel — live system diagnostics</p>
        </div>
        <button className="btn btn-ghost" onClick={fetchSystemInfo}>
          <RefreshCw size={16} /> Refresh Status
        </button>
      </div>

      <div className="grid-2">
        <div className="glass-card">
          <div className="section-header">
            <div className="section-title"><Shield size={18} /> Recognition Engine</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="input-group">
              <label className="input-label">Detection Model</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                YuNet (OpenCV DNN) — Score Threshold: {systemInfo?.detection_threshold ?? '...'}
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Recognition Model</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                SFace (ONNX) — Cosine Threshold: {systemInfo?.recognition_threshold ?? '...'}
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Engine Status</label>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <span className={`badge ${systemInfo?.recognition_ready ? 'badge-green' : 'badge-red'}`}>
                  Recognition: {systemInfo?.recognition_ready ? 'Active' : 'Not Trained'}
                </span>
                <span className={`badge ${systemInfo?.liveness_ready ? 'badge-green' : 'badge-amber'}`}>
                  Liveness: {systemInfo?.liveness_ready ? 'Active' : 'Unavailable'}
                </span>
                <span className={`badge ${systemInfo?.analysis_ready ? 'badge-green' : 'badge-amber'}`}>
                  DeepFace: {systemInfo?.analysis_ready ? 'Active' : 'Not Installed'}
                </span>
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Enrolled Data</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {loading ? 'Loading...' : (
                  <>
                    <strong style={{ color: 'var(--text-primary)' }}>{systemInfo?.enrolled_people || 0}</strong> people enrolled · 
                    <strong style={{ color: 'var(--text-primary)' }}> {systemInfo?.total_features || 0}</strong> feature vectors stored
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="glass-card">
          <div className="section-header">
            <div className="section-title"><Server size={18} /> System Architecture</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <div className="input-group">
              <label className="input-label">Backend Framework</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                FastAPI + Uvicorn (ASGI)
              </div>
            </div>
            
            <div className="input-group">
              <label className="input-label">Frontend Framework</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                React 18 + Vite (Static Build served by FastAPI)
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Database</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                SQLite (SQLAlchemy ORM)
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">ML Pipeline</label>
              <div style={{ padding: '10px 14px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                OpenCV DNN (YuNet + SFace ONNX models)
              </div>
            </div>
          </div>
        </div>

        <div className="glass-card" style={{ gridColumn: '1 / -1' }}>
          <div className="section-header">
            <div className="section-title"><Database size={18} /> Storage & Database</div>
          </div>
          <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: '300px', display: 'flex', alignItems: 'center', gap: '16px', background: 'var(--bg-elevated)', padding: '16px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
              <HardDrive size={32} color="var(--accent-blue)" />
              <div>
                <div style={{ fontSize: '0.9rem', fontWeight: '600', color: 'var(--text-primary)' }}>Storage Utilization</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                  {loading ? 'Calculating...' : systemInfo?.total_size_display || '0 MB'} used
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  {loading ? '' : (
                    <>
                      DB: {((systemInfo?.db_size_bytes || 0) / 1024).toFixed(1)} KB · 
                      Dataset: {((systemInfo?.dataset_size_bytes || 0) / 1024).toFixed(1)} KB
                    </>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
