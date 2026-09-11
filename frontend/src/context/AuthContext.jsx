import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('facevault_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const res = await fetch('/api/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
      } else {
        logout();
      }
    } catch (err) {
      console.error("Failed to fetch user", err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const body = new URLSearchParams();
      body.append('username', username);
      body.append('password', password);

      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      });
      
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('facevault_token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        let errorMsg = 'Invalid credentials';
        try {
          const error = await res.json();
          if (error && error.detail) errorMsg = error.detail;
        } catch {
          errorMsg = res.status === 404 
            ? 'Backend API not reachable (404). Ensure local backend is running on http://localhost:8000'
            : `Server error (${res.status})`;
        }
        return { success: false, message: errorMsg };
      }
    } catch (err) {
      return { 
        success: false, 
        message: 'Cannot connect to backend server. Make sure the local server is running on http://localhost:8000' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('facevault_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
