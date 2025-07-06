import React, { useState, useEffect } from 'react';
import './App.css';
import AuthForm from './components/AuthForm';
import Dashboard from './components/Dashboard';
import apiClient from './utils/apiClient';

function App() {
  const [sessionId, setSessionId] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check for saved session on component mount
  useEffect(() => {
    const savedSessionId = localStorage.getItem('eve_session_id');
    if (savedSessionId) {
      setSessionId(savedSessionId);
      setIsAuthenticated(true);
      apiClient.setSession(savedSessionId);
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

  return (
    <div className="app-container">
      <nav className="navbar navbar-expand-lg navbar-custom">
        <div className="container">
          <span className="navbar-brand text-dark-custom fs-3 fw-light">
            Eve
          </span>
          {isAuthenticated && (
            <button className="btn btn-outline-secondary btn-sm" onClick={handleLogout}>
              End Session
            </button>
          )}
        </div>
      </nav>
      
      <div className="container py-5">
        <div className="row justify-content-center">
          <div className="col-12 col-md-8 col-lg-6">
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
