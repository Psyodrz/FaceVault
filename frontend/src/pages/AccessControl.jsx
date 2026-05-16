import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Users, UserPlus, Shield, ShieldAlert, Trash2, Power, History, Search, Filter, Monitor } from 'lucide-react';

const AccessControl = () => {
  const { token } = useAuth();
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('users');
  const [showAddModal, setShowAddModal] = useState(false);

  // Form State
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newRole, setNewRole] = useState('visitor');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [uRes, aRes] = await Promise.all([
        fetch('/api/users', { headers: { 'Authorization': `Bearer ${token}` } }),
        fetch('/api/audit-logs', { headers: { 'Authorization': `Bearer ${token}` } })
      ]);

      if (uRes.ok) setUsers(await uRes.json());
      if (aRes.ok) setAuditLogs(await aRes.json());
    } catch (err) {
      console.error("Failed to load access control data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username: newUsername, password: newPassword, role: newRole })
      });

      if (res.ok) {
        setShowAddModal(false);
        setNewUsername('');
        setNewPassword('');
        fetchData();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to create user");
      }
    } catch (err) {
      setError("Network error");
    }
  };

  const toggleStatus = async (id, currentActive) => {
    try {
      const res = await fetch(`/api/users/${id}/status?active=${!currentActive}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) fetchData();
    } catch (err) {
      console.error("Status toggle failed");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Permanently delete this user account?")) return;
    try {
      const res = await fetch(`/api/users/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) fetchData();
    } catch (err) {
      console.error("Deletion failed");
    }
  };

  return (
    <div className="access-control">
      <div className="page-header">
        <div>
          <h1>Security Console</h1>
          <p className="page-subtitle">Manage operator access and audit system activity</p>
        </div>
        <div className="tab-switcher">
          <button 
            className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            <Users size={16} /> User Registry
          </button>
          <button 
            className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            <History size={16} /> Audit Trail
          </button>
        </div>
      </div>

      {activeTab === 'users' ? (
        <div className="users-section">
          <div className="action-bar" style={{ marginBottom: '20px', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
              <UserPlus size={16} /> Provision New Account
            </button>
          </div>

          <div className="glass-card" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Operator</th>
                  <th>Role</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan="5" style={{ textAlign: 'center', padding: '32px' }}>Accessing encrypted registry...</td></tr>
                ) : users.map(user => (
                  <tr key={user.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div className={`avatar-circle ${user.role}`}>
                          {user.username[0].toUpperCase()}
                        </div>
                        <span style={{ fontWeight: '600' }}>{user.username}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`role-badge ${user.role}`}>
                        {user.role === 'super_admin' ? <Shield size={12} /> : user.role === 'admin' ? <ShieldAlert size={12} /> : <Monitor size={12} />}
                        {user.role.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="mono" style={{ fontSize: '0.8rem' }}>
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td>
                      <span className={`badge ${user.is_active ? 'badge-green' : 'badge-red'}`}>
                        {user.is_active ? 'ACTIVE' : 'LOCKED'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          className="icon-btn" 
                          onClick={() => toggleStatus(user.id, user.is_active)}
                          title={user.is_active ? "Lock Account" : "Unlock Account"}
                          disabled={user.role === 'super_admin'}
                        >
                          <Power size={16} color={user.is_active ? 'var(--warning)' : 'var(--success)'} />
                        </button>
                        <button 
                          className="icon-btn" 
                          onClick={() => handleDelete(user.id)}
                          title="Revoke Access"
                          style={{ color: 'var(--danger)' }}
                          disabled={user.role === 'super_admin'}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="audit-section">
          <div className="glass-card" style={{ padding: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Operator</th>
                  <th>Action</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan="4" style={{ textAlign: 'center', padding: '32px' }}>Retrieving secure logs...</td></tr>
                ) : auditLogs.length === 0 ? (
                  <tr><td colSpan="4" style={{ textAlign: 'center', padding: '32px' }}>No system activity recorded yet.</td></tr>
                ) : auditLogs.map(log => (
                  <tr key={log.id}>
                    <td className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td style={{ fontWeight: '600' }}>{log.username}</td>
                    <td>
                      <span className="badge badge-blue" style={{ fontSize: '0.7rem' }}>{log.action}</span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showAddModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && setShowAddModal(false)}>
          <div className="glass-card modal-content" style={{ maxWidth: '400px', width: '100%', padding: '24px' }}>
            <h2 style={{ marginBottom: '20px' }}>Provision New Account</h2>
            <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div className="input-group">
                <label className="input-label">Username</label>
                <input 
                  type="text" 
                  className="input" 
                  value={newUsername} 
                  onChange={e => setNewUsername(e.target.value)}
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Initial Passcode</label>
                <input 
                  type="password" 
                  className="input" 
                  value={newPassword} 
                  onChange={e => setNewPassword(e.target.value)}
                  required 
                />
              </div>
              <div className="input-group">
                <label className="input-label">Authorization Role</label>
                <select 
                  className="input" 
                  value={newRole} 
                  onChange={e => setNewRole(e.target.value)}
                >
                  <option value="visitor">Visitor (View Only)</option>
                  <option value="admin">Admin (Operational Control)</option>
                </select>
              </div>
              {error && <p style={{ color: 'var(--danger)', fontSize: '0.8rem' }}>{error}</p>}
              <div style={{ display: 'flex', gap: '12px', marginTop: '10px' }}>
                <button type="button" className="btn btn-ghost" onClick={() => setShowAddModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Account</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccessControl;
