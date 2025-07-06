import React, { useState, useEffect } from 'react';
import axios from 'axios';

const AuthForm = ({ onAuthSuccess }) => {
  const [authMethod, setAuthMethod] = useState('oauth2');
  const [formData, setFormData] = useState({
    url: '',
    client_id: '',
    client_secret: '',
    username: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Check for saved auth data on component mount
  useEffect(() => {
    const savedAuthData = localStorage.getItem('eve_auth_data');
    if (savedAuthData) {
      try {
        const authData = JSON.parse(savedAuthData);
        // Auto-fill the URL and auth method from saved data
        setFormData(prev => ({
          ...prev,
          url: authData.url || ''
        }));
        setAuthMethod(authData.authMethod || 'oauth2');
      } catch (error) {
        console.error('Error parsing saved auth data:', error);
        localStorage.removeItem('eve_auth_data');
      }
    }
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear messages when user starts typing
    if (error) setError('');
    if (success) setSuccess('');
  };

  const handleAuthMethodChange = (method) => {
    setAuthMethod(method);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setSuccess('');

    try {
      const payload = {
        url: formData.url,
        auth_method: authMethod,
        ...(authMethod === 'oauth2' 
          ? { client_id: formData.client_id, client_secret: formData.client_secret }
          : { username: formData.username, password: formData.password }
        )
      };

      const response = await axios.post('/api/authenticate', payload);
      
      if (response.data.success) {
        setSuccess('Authentication successful!');
        
        // Save auth data to localStorage
        const authData = {
          sessionId: response.data.session_id,
          url: formData.url,
          authMethod: authMethod,
          timestamp: Date.now()
        };
        
        // Don't save sensitive credentials, just the session info
        localStorage.setItem('eve_auth_data', JSON.stringify(authData));
        
        setTimeout(() => {
          onAuthSuccess(response.data.session_id);
        }, 1000);
      }
    } catch (err) {
      setError(
        err.response?.data?.error || 
        err.response?.data?.message || 
        'Authentication failed. Please check your credentials.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="card auth-card">
      <div className="card-body p-4">
        <h2 className="card-title text-center mb-4">Connect to Eve</h2>
        
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}
        
        {success && (
          <div className="alert alert-success" role="alert">
            {success}
          </div>
        )}
        
        {/* Authentication Method Selector */}
        <div className="mb-4">
          <div className="btn-group w-100" role="group" aria-label="Authentication method">
            <button
              type="button"
              className={`btn ${authMethod === 'oauth2' ? 'btn-primary' : 'btn-outline-primary'}`}
              onClick={() => handleAuthMethodChange('oauth2')}
            >
              OAuth2 Client
            </button>
            <button
              type="button"
              className={`btn ${authMethod === 'username_password' ? 'btn-primary' : 'btn-outline-primary'}`}
              onClick={() => handleAuthMethodChange('username_password')}
            >
              Username/Password
            </button>
          </div>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label htmlFor="url" className="form-label">Jamf Pro URL</label>
            <input
              type="url"
              className="form-control"
              id="url"
              name="url"
              value={formData.url}
              onChange={handleChange}
              placeholder="https://your-jamf-instance.jamfcloud.com"
              required
            />
          </div>
          
          {authMethod === 'oauth2' ? (
            <>
              <div className="mb-3">
                <label htmlFor="client_id" className="form-label">Client ID</label>
                <input
                  type="text"
                  className="form-control"
                  id="client_id"
                  name="client_id"
                  value={formData.client_id}
                  onChange={handleChange}
                  placeholder="Enter your API client ID"
                  required
                />
              </div>
              
              <div className="mb-3">
                <label htmlFor="client_secret" className="form-label">Client Secret</label>
                <input
                  type="password"
                  className="form-control"
                  id="client_secret"
                  name="client_secret"
                  value={formData.client_secret}
                  onChange={handleChange}
                  placeholder="Enter your API client secret"
                  required
                />
              </div>
            </>
          ) : (
            <>
              <div className="mb-3">
                <label htmlFor="username" className="form-label">Username</label>
                <input
                  type="text"
                  className="form-control"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleChange}
                  placeholder="Enter your username"
                  required
                />
              </div>
              
              <div className="mb-3">
                <label htmlFor="password" className="form-label">Password</label>
                <input
                  type="password"
                  className="form-control"
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="Enter your password"
                  required
                />
              </div>
            </>
          )}
          
          <button 
            type="submit" 
            className="btn btn-primary w-100" 
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <span className="loading-spinner me-2"></span>
                Authenticating...
              </>
            ) : (
              'Connect'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthForm;
