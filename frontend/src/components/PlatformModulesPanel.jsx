import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import {
  Monitor,
  LayoutGrid,
  User,
  Shield,
  CalendarClock,
  X,
  ArrowRight,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import './PlatformModulesPanel.css';

export const PLATFORM_MODULES = [
  {
    name: 'Live Monitor',
    icon: Monitor,
    path: '/monitor',
    desc: 'Real-time neural stream',
    requiresAuth: true,
  },
  {
    name: 'Analytics',
    icon: LayoutGrid,
    path: '/analytics',
    desc: 'Data visualization hub',
    requiresAuth: true,
  },
  {
    name: 'Personnel',
    icon: User,
    path: '/personnel',
    desc: 'Facial registry',
    requiresAuth: true,
  },
  {
    name: 'Privacy Shield',
    icon: Shield,
    path: '/privacy',
    desc: 'PII anonymization',
    requiresAuth: true,
  },
  {
    name: 'Attendance',
    icon: CalendarClock,
    path: '/attendance',
    desc: 'Check-in logs and reports',
    requiresAuth: false,
  },
];

const PlatformModulesPanel = ({ open, onClose }) => {
  const { user } = useAuth();

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', onKeyDown);
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div className="modules-panel-overlay" onClick={onClose} role="presentation">
      <div
        className="modules-panel glass-card"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modules-panel-title"
      >
        <div className="modules-panel-header">
          <h3 id="modules-panel-title">Platform Modules</h3>
          <button
            type="button"
            className="modules-panel-close icon-btn"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>
        <div className="modules-panel-list">
          {PLATFORM_MODULES.map((m) => {
            const Icon = m.icon;
            const to = !user && m.requiresAuth ? '/login' : m.path;
            return (
              <Link
                key={m.path}
                to={to}
                className="modules-panel-item"
                onClick={onClose}
              >
                <div className="modules-panel-icon">
                  <Icon size={18} />
                </div>
                <div className="modules-panel-text">
                  <span className="modules-panel-name">{m.name}</span>
                  <span className="modules-panel-desc">{m.desc}</span>
                </div>
                <ArrowRight size={16} className="modules-panel-arrow" aria-hidden />
              </Link>
            );
          })}
        </div>
        {!user && (
          <p className="modules-panel-hint">
            Sign in to access secured modules.
          </p>
        )}
      </div>
    </div>,
    document.body
  );
};

export default PlatformModulesPanel;
