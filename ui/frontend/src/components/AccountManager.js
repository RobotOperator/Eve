import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';

const AccountManager = ({ sessionId, onBack }) => {
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('users');
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiClient.setSession(sessionId);
    loadAccounts();
  }, [sessionId]);

  const loadAccounts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get('/api/accounts');
      
      if (response.ok) {
        const userData = await response.json();
        setUsers(userData || []);
        
        // Also load groups
        const groupResponse = await apiClient.get('/api/groups');
        
        if (groupResponse.ok) {
          const groupData = await groupResponse.json();
          setGroups(groupData || []);
        } else {
          setError('Failed to load groups');
        }
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load accounts');
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
      setError('Network error while loading accounts');
    } finally {
      setLoading(false);
    }
  };

  const getGroupDetails = async (id) => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get(`/api/groups/${id}`);
      
      if (response.ok) {
        const data = await response.json();
        setSelectedGroup(data.group || data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to get group details');
      }
    } catch (error) {
      console.error('Error getting group details:', error);
      setError('Network error while getting group details');
    } finally {
      setLoading(false);
    }
  };

  if (selectedGroup) {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Group Details</h3>
          <div>
            <button className="btn btn-secondary me-2" onClick={() => setSelectedGroup(null)}>
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
              <p><strong>Name:</strong> {selectedGroup.name}</p>
              <p><strong>Access Level:</strong> {selectedGroup.access_level}</p>
              <p><strong>Privilege Set:</strong> {selectedGroup.privilege_set}</p>
              <p><strong>Site:</strong> {selectedGroup.site?.name || 'N/A'}</p>
            </div>
            <div className="col-md-6">
              <h5>Privileges</h5>
              {selectedGroup.privileges && (
                <ul className="list-group list-group-flush">
                  <li className="list-group-item">
                    <strong>JSS Objects:</strong> {selectedGroup.privileges.jss_objects?.join(', ') || 'None'}
                  </li>
                  <li className="list-group-item">
                    <strong>JSS Settings:</strong> {selectedGroup.privileges.jss_settings?.join(', ') || 'None'}
                  </li>
                  <li className="list-group-item">
                    <strong>JSS Actions:</strong> {selectedGroup.privileges.jss_actions?.join(', ') || 'None'}
                  </li>
                </ul>
              )}
            </div>
          </div>
          
          {selectedGroup.members && selectedGroup.members.length > 0 && (
            <div className="mt-4">
              <h5>Members</h5>
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedGroup.members.map((member) => (
                      <tr key={member.id}>
                        <td>{member.id}</td>
                        <td>{member.name}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h3 className="mb-0">Account Management</h3>
        <div>
          <button className="btn btn-primary me-2" onClick={loadAccounts} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button className="btn btn-outline-secondary" onClick={onBack}>
            Back to Dashboard
          </button>
        </div>
      </div>
      
      <div className="card-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            <strong>Error:</strong> {error}
            <button 
              type="button" 
              className="btn-close float-end" 
              onClick={() => setError('')}
            ></button>
          </div>
        )}
        
        <ul className="nav nav-tabs mb-3">
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'users' ? 'active' : ''}`}
              onClick={() => setActiveTab('users')}
            >
              Users ({users.length})
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-link ${activeTab === 'groups' ? 'active' : ''}`}
              onClick={() => setActiveTab('groups')}
            >
              Groups ({groups.length})
            </button>
          </li>
        </ul>

        {loading && users.length === 0 && groups.length === 0 ? (
          <div className="text-center">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-2">Loading accounts...</p>
          </div>
        ) : (
          <>
            {activeTab === 'users' && (
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Full Name</th>
                      <th>Email</th>
                      <th>Access Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.id}</td>
                        <td>{user.name}</td>
                        <td>{user.full_name}</td>
                        <td>{user.email || 'N/A'}</td>
                        <td>
                          <span className={`badge ${user.access_level === 'Full Access' ? 'bg-danger' : 'bg-primary'}`}>
                            {user.access_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'groups' && (
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Access Level</th>
                      <th>Privilege Set</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((group) => (
                      <tr key={group.id}>
                        <td>{group.id}</td>
                        <td>{group.name}</td>
                        <td>
                          <span className={`badge ${group.access_level === 'Full Access' ? 'bg-danger' : 'bg-primary'}`}>
                            {group.access_level}
                          </span>
                        </td>
                        <td>{group.privilege_set}</td>
                        <td>
                          <button 
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => getGroupDetails(group.id)}
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
          </>
        )}

        {((activeTab === 'users' && users.length === 0) || (activeTab === 'groups' && groups.length === 0)) && !loading && (
          <div className="alert alert-info">
            No {activeTab} found.
          </div>
        )}
      </div>
    </div>
  );
};

export default AccountManager;
