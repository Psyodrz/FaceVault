import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import LiveMonitor from './pages/LiveMonitor';
import Personnel from './pages/Personnel';
import Attendance from './pages/Attendance';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import PrivacyShield from './pages/PrivacyShield';
import Settings from './pages/Settings';
import AccessControl from './pages/AccessControl';
import LoginPage from './pages/LoginPage';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import './App.css';

const ProtectedRoute = ({ children, requiredRole, requireLogin = true }) => {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="auth-container">Loading Sentinel OS...</div>;
  
  // If login is strictly required and user is not logged in
  if (requireLogin && !user) {
    return <Navigate to="/login" />;
  }
  
  // If user is logged in, check role. (Guest user has no role)
  if (requiredRole && user) {
    if (user.role !== requiredRole && user.role !== 'super_admin') {
      return <Navigate to="/" />; // Redirect if not enough privileges
    }
  }
  
  return children;
};

const AppLayout = ({ children }) => {
  const [navOpen, setNavOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    document.body.style.overflow = navOpen ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [navOpen]);

  return (
    <div className={`app-layout${navOpen ? ' nav-open' : ''}`}>
      <button
        type="button"
        className="sidebar-backdrop"
        aria-label="Close navigation"
        onClick={() => setNavOpen(false)}
      />
      <Sidebar onNavigate={() => setNavOpen(false)} />
      <div className="main-content">
        <Header onMenuToggle={() => setNavOpen((open) => !open)} navOpen={navOpen} />
        <div className="page-container">
          {children}
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            
            {/* Public/Guest Routes */}
            <Route path="/" element={<ProtectedRoute requireLogin={false}><AppLayout><Dashboard /></AppLayout></ProtectedRoute>} />
            <Route path="/attendance" element={<ProtectedRoute requireLogin={false}><AppLayout><Attendance /></AppLayout></ProtectedRoute>} />
            
            {/* Admin & Super Admin Routes */}
            <Route path="/monitor" element={<ProtectedRoute><AppLayout><LiveMonitor /></AppLayout></ProtectedRoute>} />
            <Route path="/alerts" element={<ProtectedRoute><AppLayout><Alerts /></AppLayout></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><AppLayout><Analytics /></AppLayout></ProtectedRoute>} />
            
            {/* Super Admin Only Routes */}
            <Route path="/personnel" element={<ProtectedRoute requiredRole="super_admin"><AppLayout><Personnel /></AppLayout></ProtectedRoute>} />
            <Route path="/access-control" element={<ProtectedRoute requiredRole="super_admin"><AppLayout><AccessControl /></AppLayout></ProtectedRoute>} />
            <Route path="/privacy" element={<ProtectedRoute requiredRole="super_admin"><AppLayout><PrivacyShield /></AppLayout></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute requireLogin={false} requiredRole="super_admin"><AppLayout><Settings /></AppLayout></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;
