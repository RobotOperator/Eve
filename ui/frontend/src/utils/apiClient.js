// API utilities with automatic token refresh
class ApiClient {
  constructor() {
    this.baseURL = '';
    this.sessionId = null;
    this.isRefreshing = false;
    this.failedQueue = [];
  }

  setSession(sessionId) {
    this.sessionId = sessionId;
  }

  async request(endpoint, options = {}) {
    const config = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers
      },
      ...options
    };

    if (this.sessionId) {
      config.headers['X-Session-ID'] = this.sessionId;
    }

    try {
      const response = await fetch(endpoint, config);
      
      // If we get a 401, try to refresh the token
      if (response.status === 401 && !this.isRefreshing) {
        return this.handleTokenRefresh(endpoint, config);
      }
      
      return response;
    } catch (error) {
      throw error;
    }
  }

  async handleTokenRefresh(endpoint, originalConfig) {
    if (this.isRefreshing) {
      // If already refreshing, queue this request
      return new Promise((resolve, reject) => {
        this.failedQueue.push({ resolve, reject, endpoint, config: originalConfig });
      });
    }

    this.isRefreshing = true;

    try {
      console.log('🔄 Token expired, attempting refresh...');
      
      // Get stored auth data from localStorage
      const authData = localStorage.getItem('eve_auth_data');
      if (!authData) {
        throw new Error('No authentication data found');
      }

      const { url, authMethod, sessionId } = JSON.parse(authData);
      
      // Check if we have credentials stored for re-authentication
      const storedCreds = this.getStoredCredentials();
      if (!storedCreds) {
        throw new Error('No credentials available for refresh');
      }

      // Re-authenticate
      const refreshPayload = {
        url: storedCreds.url,
        auth_method: storedCreds.authMethod,
        ...storedCreds.credentials
      };

      const refreshResponse = await fetch('/api/authenticate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(refreshPayload)
      });

      if (!refreshResponse.ok) {
        throw new Error('Token refresh failed');
      }

      const refreshData = await refreshResponse.json();
      
      if (refreshData.success) {
        console.log('✅ Token refreshed successfully');
        
        // Show success notification
        this.showNotification('Token refreshed successfully', 'success');
        
        // Update stored session
        this.sessionId = refreshData.session_id;
        
        // Update localStorage
        const newAuthData = {
          sessionId: refreshData.session_id,
          url: storedCreds.url,
          authMethod: storedCreds.authMethod,
          timestamp: Date.now()
        };
        localStorage.setItem('eve_auth_data', JSON.stringify(newAuthData));
        localStorage.setItem('eve_session_id', refreshData.session_id);

        // Retry the original request
        originalConfig.headers['X-Session-ID'] = refreshData.session_id;
        const retryResponse = await fetch(endpoint, originalConfig);

        // Process queued requests
        this.processQueue(null, refreshData.session_id);
        
        return retryResponse;
      } else {
        throw new Error('Authentication failed');
      }
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      
      // Show error notification
      this.showNotification('Session expired. Please log in again.', 'error');
      
      // Process queued requests with error
      this.processQueue(error, null);
      
      // Clear auth data and redirect to login
      this.clearAuth();
      
      throw error;
    } finally {
      this.isRefreshing = false;
    }
  }

  showNotification(message, type = 'info') {
    // Create a simple notification div
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} position-fixed`;
    notification.style.cssText = `
      top: 20px;
      right: 20px;
      z-index: 9999;
      min-width: 300px;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    notification.innerHTML = `
      ${message}
      <button type="button" class="btn-close float-end" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 5000);
  }

  processQueue(error, token) {
    this.failedQueue.forEach(({ resolve, reject, endpoint, config }) => {
      if (error) {
        reject(error);
      } else {
        config.headers['X-Session-ID'] = token;
        resolve(fetch(endpoint, config));
      }
    });
    
    this.failedQueue = [];
  }

  getStoredCredentials() {
    // Try to get credentials from sessionStorage (more secure)
    const creds = sessionStorage.getItem('eve_temp_credentials');
    if (creds) {
      return JSON.parse(creds);
    }
    
    // Fallback: prompt user for credentials if none stored
    return null;
  }

  clearAuth() {
    localStorage.removeItem('eve_session_id');
    localStorage.removeItem('eve_auth_data');
    sessionStorage.removeItem('eve_temp_credentials');
    this.sessionId = null;
    
    // Reload page to show login form
    window.location.reload();
  }

  // Convenience methods for common HTTP verbs
  async get(endpoint, params = {}) {
    const query = new URLSearchParams(params).toString();
    const url = query ? `${endpoint}?${query}` : endpoint;
    return this.request(url);
  }

  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  async delete(endpoint) {
    return this.request(endpoint, {
      method: 'DELETE'
    });
  }
}

// Create a singleton instance
const apiClient = new ApiClient();

export default apiClient;
