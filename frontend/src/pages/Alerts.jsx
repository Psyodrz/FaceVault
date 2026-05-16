import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, AlertTriangle, Info, CheckCircle, Search, ShieldCheck } from 'lucide-react';

const Alerts = () => {
  const { token, user } = useAuth();
  const [filter, setFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filter === 'pending') params.append('status', 'pending');
      else if (filter === 'critical' || filter === 'warning') params.append('severity', filter);

      const res = await fetch(`/api/threats?${params.toString()}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAlerts(data);
      }
    } catch (err) {
      console.error("Failed to load threats");
    } finally {
      setLoading(false);
    }
  }, [token, filter]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const handleAcknowledge = async (id) => {
    try {
      await fetch(`/api/threats/${id}/status?status=acknowledged`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchAlerts();
    } catch (err) {
      console.error("Failed to acknowledge threat");
    }
  };

  const handleResolve = async (id) => {
    try {
      await fetch(`/api/threats/${id}/status?status=resolved`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchAlerts();
    } catch (err) {
      console.error("Failed to resolve threat");
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return a.title.toLowerCase().includes(q) || a.desc.toLowerCase().includes(q) || a.zone.toLowerCase().includes(q);
    }
    return true;
  });

  return (
    <div className="alerts">
      <div className="page-header">
        <div>
          <h1>Threat Intelligence</h1>
          <p className="page-subtitle">Real-time behavioral anomalies and security incidents</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <div className="search-bar">
            <Search size={16} />
            <input 
              type="text" 
              placeholder="Search logs..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>
          <select className="input" style={{ width: '150px' }} value={filter} onChange={e => setFilter(e.target.value)}>
            <option value="all">All Alerts</option>
            <option value="pending">Pending</option>
            <option value="critical">Critical Only</option>
            <option value="warning">Warnings</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {loading ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
            <p>Loading threat data...</p>
          </div>
        ) : filteredAlerts.length === 0 ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
            <ShieldCheck size={48} style={{ opacity: 0.2, marginBottom: '16px' }} />
            <p style={{ fontSize: '1.1rem', fontWeight: '500' }}>All Clear</p>
            <p style={{ fontSize: '0.85rem' }}>No threat events recorded. The system will automatically log unknown face detections and security anomalies here.</p>
          </div>
        ) : (
          filteredAlerts.map(alert => (
            <div key={alert.id} className="glass-card" style={{ 
              display: 'flex', 
              gap: '20px', 
              borderLeft: `4px solid ${
                alert.severity === 'critical' ? 'var(--danger)' : 
                alert.severity === 'warning' ? 'var(--warning)' : 
                'var(--accent-blue)'
              }`
            }}>
              <div style={{ flex: '0 0 auto', paddingTop: '4px' }}>
                {alert.severity === 'critical' && <ShieldAlert size={24} color="var(--danger)" />}
                {alert.severity === 'warning' && <AlertTriangle size={24} color="var(--warning)" />}
                {alert.severity === 'info' && <Info size={24} color="var(--accent-blue)" />}
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <h3 style={{ fontSize: '1rem', color: 'var(--text-primary)', margin: 0 }}>{alert.title}</h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{alert.time}</span>
                    <span className={`badge ${
                      alert.status === 'pending' ? 'badge-red' : 
                      alert.status === 'acknowledged' ? 'badge-amber' : 'badge-green'
                    }`}>
                      {alert.status.toUpperCase()}
                    </span>
                  </div>
                </div>
                
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                  {alert.desc}
                </p>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <strong>Location:</strong> {alert.zone}
                  </div>
                  
                  {alert.status !== 'resolved' && user?.role === 'super_admin' && (
                    <div style={{ display: 'flex', gap: '8px' }}>
                      {alert.status === 'pending' && (
                        <button className="btn btn-ghost btn-sm" onClick={() => handleAcknowledge(alert.id)}>
                          Acknowledge
                        </button>
                      )}
                      <button className="btn btn-primary btn-sm" onClick={() => handleResolve(alert.id)}>
                        <CheckCircle size={14} /> Resolve
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Alerts;
