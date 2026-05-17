import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Bell, 
  Search, 
  Monitor,
  Moon,
  Sun,
  Clock,
  ShieldCheck,
  LayoutGrid,
  Menu,
  X
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import PlatformModulesPanel from './PlatformModulesPanel';
import './Header.css';

const Header = ({ onMenuToggle, navOpen }) => {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();
  const [scrolled, setScrolled] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [threats, setThreats] = useState([]);

  const [showModules, setShowModules] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowSearch(true);
      }
      if (e.key === 'Escape') {
        setShowSearch(false);
        setShowModules(false);
        setShowNotifications(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', handleScroll);
    
    fetchThreats();
    const interval = setInterval(fetchThreats, 30000);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('scroll', handleScroll);
      clearInterval(interval);
    };
  }, []);

  const fetchThreats = async () => {
    try {
      const res = await fetch('/api/threats?status=pending');
      if (res.ok) {
        const data = await res.json();
        setThreats(data.slice(0, 5));
      }
    } catch (err) {
      console.error("Notification polling failed");
    }
  };

  return (
    <header className={`header ${scrolled ? 'scrolled' : ''}`}>
      <div className="header-left">
        <button
          type="button"
          className="mobile-menu-btn icon-btn"
          onClick={onMenuToggle}
          aria-label={navOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={navOpen}
        >
          {navOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
        <div className="breadcrumb">
          <Monitor size={14} className="bread-icon" />
          <span className="bread-root">Sentinel</span>
          <span className="bread-sep">/</span>
          <span className="bread-current">{window.location.pathname === '/' ? 'Console' : 'Module'}</span>
        </div>
      </div>

      <div className="header-actions">
        <div className="action-group glass-action">
          <button
            type="button"
            className="icon-btn"
            onClick={() => setShowModules(true)}
            aria-label="Platform modules"
            aria-haspopup="dialog"
          >
            <LayoutGrid size={18} />
          </button>
          
          <button type="button" className="icon-btn" onClick={() => setShowSearch(true)}><Search size={18} /></button>
        </div>

        {showSearch && (
          <div className="search-overlay fade-in" onClick={() => setShowSearch(false)}>
            <div className="search-modal glass-card" onClick={e => e.stopPropagation()}>
              <div className="search-modal-header">
                <Search size={20} />
                <input 
                  autoFocus 
                  type="text" 
                  placeholder="Search personnel, logs, or threats..." 
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                />
                <span className="search-key">ESC</span>
              </div>
              <div className="search-results">
                {searchQuery ? (
                  <div className="empty-search">Searching for "{searchQuery}"...</div>
                ) : (
                  <div className="search-hints">
                    <p>Recent Searches</p>
                    <div className="hint-list">
                      <span>Aditya</span>
                      <span>Unknown Face Detected</span>
                      <span>Critical Alerts</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="action-group glass-action">
          <button 
            type="button"
            className="icon-btn" 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            title="Toggle Environmental Mode"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>

        <div className="action-group">
          <div className="notification-wrapper">
            <button 
              type="button"
              className={`icon-btn ${threats.length > 0 ? 'has-alerts' : ''}`}
              onClick={() => setShowNotifications(!showNotifications)}
            >
              <Bell size={20} />
              {threats.length > 0 && <span className="notification-badge pulse">{threats.length}</span>}
            </button>

            {showNotifications && (
              <div className="notification-dropdown glass-card fade-in">
                <div className="dropdown-header">
                  <h3>Security Alerts</h3>
                  <span className="badge badge-blue">{threats.length} PENDING</span>
                </div>
                <div className="dropdown-list">
                  {threats.length === 0 ? (
                    <div className="empty-notif">
                      <ShieldCheck size={32} />
                      <p>System Nominal. No threats detected.</p>
                    </div>
                  ) : (
                    threats.map(t => (
                      <div key={t.id} className="notif-item">
                        <div className={`notif-indicator ${t.severity}`}></div>
                        <div className="notif-body">
                          <p className="notif-title">{t.title}</p>
                          <div className="notif-meta">
                            <span><Clock size={10} /> {t.time}</span>
                            <span>{t.zone}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <div className="dropdown-footer">
                  <Link to="/alerts">View Forensic Logs</Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {!user ? (
          <Link to="/login" className="btn btn-primary btn-sm">
            Personnel Login
          </Link>
        ) : (
          <div className="user-profile">
            <div className="user-info">
              <span className="user-name">{user.username}</span>
              <span className="user-role">{user.role.replace('_', ' ')}</span>
            </div>
            <div className="user-avatar">
              {user.username.charAt(0).toUpperCase()}
            </div>
          </div>
        )}
      </div>

      <PlatformModulesPanel open={showModules} onClose={() => setShowModules(false)} />
    </header>
  );
};

export default Header;
