import React, { useState, useEffect } from 'react';

const ApiManager = ({ sessionId, onBack }) => {
  const [apiRoles, setApiRoles] = useState([]);
  const [apiClients, setApiClients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('roles');
  const [selectedRole, setSelectedRole] = useState(null);

  useEffect(() => {
    loadApiData();
  }, []);

  const loadApiData = async () => {
    setLoading(true);
    try {
      // Load API roles
      const rolesResponse = await fetch('/api/api-roles', {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (rolesResponse.ok) {
        const rolesData = await rolesResponse.json();
        setApiRoles(rolesData.results || []);
      }

      // Load API clients
      const clientsResponse = await fetch('/api/api-clients', {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (clientsResponse.ok) {
        const clientsData = await clientsResponse.json();
        setApiClients(clientsData.results || []);
      }
    } catch (error) {
      console.error('Error loading API data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRoleDetails = async (id) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/api-roles/${id}`, {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedRole(data);
      } else {
        console.error('Failed to get role details');
      }
    } catch (error) {
      console.error('Error getting role details:', error);
    } finally {
      setLoading(false);
    }
  };

  if (selectedRole) {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">API Role Details</h3>
          <div>
            <button className="btn btn-secondary me-2" onClick={() => setSelectedRole(null)}>
              Back to List
            </button>
            <button className="btn btn-outline-secondary" onClick={onBack}>
              Back to Dashboard
            </button>
          </div>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <h5>General Information</h5>
              <p><strong>ID:</strong> {selectedRole.id}</p>
              <p><strong>Display Name:</strong> {selectedRole.displayName}</p>
              <p><strong>Created:</strong> {new Date(selectedRole.createdDate).toLocaleString()}</p>
              <p><strong>Updated:</strong> {new Date(selectedRole.updatedDate).toLocaleString()}</p>
            </div>
            <div className="col-md-6">
              <h5>Privileges</h5>
              {selectedRole.privileges && selectedRole.privileges.length > 0 ? (
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  <ul className="list-group list-group-flush">
                    {selectedRole.privileges.map((privilege, index) => (
                      <li key={index} className="list-group-item">
                        {privilege}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : (
                <p className="text-muted">No privileges defined</p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h3 className="mb-0">API Management</h3>
        <div>
          <button className="btn btn-primary me-2" onClick={loadApiData} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button className="btn btn-outline-secondary" onClick={onBack}>
            Back to Dashboard
          </button>
        </div>
      </div>
      
      <div className="card-body">
        <ul className="nav nav-tabs mb-3">
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'roles' ? 'active' : ''}`}
              onClick={() => setActiveTab('roles')}
            >
              API Roles ({apiRoles.length})
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'clients' ? 'active' : ''}`}
              onClick={() => setActiveTab('clients')}
            >
              API Clients ({apiClients.length})
            </button>
          </li>
        </ul>

        {loading && apiRoles.length === 0 && apiClients.length === 0 ? (
          <div className="text-center">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-2">Loading API data...</p>
          </div>
        ) : (
          <>
            {activeTab === 'roles' && (
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Display Name</th>
                      <th>Privileges Count</th>
                      <th>Created Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiRoles.map((role) => (
                      <tr key={role.id}>
                        <td>{role.id}</td>
                        <td>{role.displayName}</td>
                        <td>
                          <span className="badge bg-info">
                            {role.privileges ? role.privileges.length : 0}
                          </span>
                        </td>
                        <td>{new Date(role.createdDate).toLocaleDateString()}</td>
                        <td>
                          <button 
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => getRoleDetails(role.id)}
                            disabled={loading}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'clients' && (
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Display Name</th>
                      <th>Client ID</th>
                      <th>Enabled</th>
                      <th>Created Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {apiClients.map((client) => (
                      <tr key={client.id}>
                        <td>{client.id}</td>
                        <td>{client.displayName}</td>
                        <td><code>{client.clientId}</code></td>
                        <td>
                          <span className={`badge ${client.enabled ? 'bg-success' : 'bg-secondary'}`}>
                            {client.enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </td>
                        <td>{new Date(client.createdDate).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}

        {((activeTab === 'roles' && apiRoles.length === 0) || (activeTab === 'clients' && apiClients.length === 0)) && !loading && (
          <div className="alert alert-info">
            No {activeTab === 'roles' ? 'API roles' : 'API clients'} found.
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiManager;
