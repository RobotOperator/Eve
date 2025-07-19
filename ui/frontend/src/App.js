import React, { useState, useEffect } from 'react';
import './App.css';
import AuthForm from './components/AuthForm';
import Dashboard from './components/Dashboard';
import apiClient from './utils/apiClient';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Check for saved session and dark mode preference on component mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('eve_session_id');
    const savedDarkMode = localStorage.getItem('eve_dark_mode') === 'true';
    
    if (savedSessionId) {
      setSessionId(savedSessionId);
      setIsAuthenticated(true);
      apiClient.setSession(savedSessionId);
    }
    
    setIsDarkMode(savedDarkMode);
    // Apply dark mode class to document
    if (savedDarkMode) {
      document.documentElement.setAttribute('data-bs-theme', 'dark');
    }
  }, []);

  const handleAuthSuccess = (newSessionId) => {
    setSessionId(newSessionId);
    setIsAuthenticated(true);
    apiClient.setSession(newSessionId);
    // Save session to localStorage
    localStorage.setItem('eve_session_id', newSessionId);
  };

  const handleLogout = () => {
    setSessionId(null);
    setIsAuthenticated(false);
    apiClient.clearAuth();
  };

  const toggleDarkMode = () => {
    const newDarkMode = !isDarkMode;
    setIsDarkMode(newDarkMode);
    
    // Save preference to localStorage
    localStorage.setItem('eve_dark_mode', newDarkMode.toString());
    
    // Apply/remove dark mode class to document
    if (newDarkMode) {
      document.documentElement.setAttribute('data-bs-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-bs-theme');
    }
  };

  return (
    <div className={`app-container ${isDarkMode ? 'dark-mode' : ''}`}>
      <nav className="navbar navbar-expand-lg navbar-custom">
        <div className="container-fluid">
          <span className="navbar-brand text-dark-custom fs-3 fw-light">
            Eve
          </span>
          <div className="d-flex align-items-center gap-2">
            <button 
              className="btn btn-outline-secondary btn-sm" 
              onClick={toggleDarkMode}
              title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDarkMode ? '☀️' : '🌙'}
            </button>
            {isAuthenticated && (
              <button className="btn btn-outline-secondary btn-sm" onClick={handleLogout}>
                End Session
              </button>
            )}
          </div>
        </div>
      </nav>
      
      <div className="container-fluid py-5">
        <div className="row justify-content-center">
          <div className="col-12 col-sm-11 col-md-10 col-lg-11 col-xl-10 col-xxl-9">
            {!isAuthenticated ? (
              <AuthForm onAuthSuccess={handleAuthSuccess} />
            ) : (
              <Dashboard sessionId={sessionId} onLogout={handleLogout} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
