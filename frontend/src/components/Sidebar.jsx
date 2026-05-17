import React, { useState, useEffect } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  CalendarClock, 
  ShieldAlert, 
  Settings, 
  LogOut, 
  ShieldCheck,
  Search
} from 'lucide-react';
import './Sidebar.css';

import logo from '../assets/logo.png';

const Sidebar = () => {
  const { logout, user } = useAuth();
  const [nodeOnline, setNodeOnline] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/api/health');
        setNodeOnline(res.ok);
      } catch {
        setNodeOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const menuItems = [
    { name: 'Dashboard', icon: <LayoutDashboard size={20} />, path: '/' },
    { name: 'Attendance Logs', icon: <CalendarClock size={20} />, path: '/attendance' },
    { name: 'Security Alerts', icon: <ShieldAlert size={20} />, path: '/alerts' },
  ];

  if (user?.role === 'super_admin') {
    menuItems.push({ name: 'Access Control', icon: <ShieldCheck size={20} />, path: '/access-control' });
  }

  return (
    <div className="sidebar">
      <Link to="/" className="sidebar-brand" style={{ textDecoration: 'none', cursor: 'pointer' }}>
        <div className="brand-logo" style={{ background: 'transparent', border: 'none' }}>
          <img src={logo} alt="FaceVault Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
        </div>
        <div className="brand-text">
          <span className="brand-name">FaceVault</span>
          <span className="brand-tag">SENTINEL PLATFORM</span>
        </div>
      </Link>

      <div className="sidebar-search">
        <div className="search-box">
          <Search size={14} className="search-icon" />
          <input type="text" placeholder="Global search..." />
          <span className="search-key">⌘K</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-group">
          <div className="nav-label">Command Center</div>
          {menuItems.map((item) => (
            <NavLink 
              key={item.path} 
              to={item.path} 
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <div className="link-icon">{item.icon}</div>
              <span>{item.name}</span>
            </NavLink>
          ))}
        </div>

        <div className="nav-group">
          <div className="nav-label">System</div>
          <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <div className="link-icon"><Settings size={20} /></div>
            <span>Global Settings</span>
          </NavLink>
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="footer-status">
          <div className={`status-indicator ${nodeOnline ? 'online' : ''}`}></div>
          <div className="status-text">
            <span className="node-id">NODE-X01</span>
            <span className="node-status">{nodeOnline ? 'Optimal' : 'Unreachable'}</span>
          </div>
        </div>
        <button onClick={logout} className="logout-btn">
          <LogOut size={18} />
          <span>Terminate Session</span>
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
