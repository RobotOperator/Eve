import React, { useState, useEffect } from 'react';
import apiClient from '../utils/apiClient';

const ScriptManager = ({ sessionId, onBack }) => {
  const [scripts, setScripts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedScript, setSelectedScript] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingScript, setEditingScript] = useState(null);
  const [newScript, setNewScript] = useState({ name: '', content: '' });
  const [error, setError] = useState('');

  useEffect(() => {
    apiClient.setSession(sessionId);
    loadScripts();
  }, [sessionId]);

  const loadScripts = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get('/api/scripts');
      
      if (response.ok) {
        const data = await response.json();
        setScripts(data.scripts || []);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load scripts');
      }
    } catch (error) {
      console.error('Error loading scripts:', error);
      setError('Network error while loading scripts');
    } finally {
      setLoading(false);
    }
  };

  const getScriptDetails = async (id) => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get(`/api/scripts/${id}`);
      
      if (response.ok) {
        const data = await response.json();
        setSelectedScript(data.script || data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to get script details');
      }
    } catch (error) {
      console.error('Error getting script details:', error);
      setError('Network error while getting script details');
    } finally {
      setLoading(false);
    }
  };

  const deleteScript = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete script "${name}"?`)) {
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiClient.delete(`/api/scripts/${id}`);
      
      if (response.ok) {
        await loadScripts(); // Refresh the list
        alert('Script deleted successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to delete script');
        alert('Failed to delete script');
      }
    } catch (error) {
      console.error('Error deleting script:', error);
      setError('Network error while deleting script');
      alert('Error deleting script');
    } finally {
      setLoading(false);
    }
  };

  const createScript = async () => {
    if (!newScript.name.trim() || !newScript.content.trim()) {
      alert('Please provide both script name and content');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiClient.post('/api/scripts', {
        name: newScript.name.trim(),
        content: newScript.content
      });
      
      if (response.ok) {
        const data = await response.json();
        await loadScripts(); // Refresh the list
        setShowCreateModal(false);
        setNewScript({ name: '', content: '' });
        alert('Script created successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create script');
        alert(`Failed to create script: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating script:', error);
      setError('Network error while creating script');
      alert('Error creating script');
    } finally {
      setLoading(false);
    }
  };

  const updateScript = async () => {
    if (!editingScript.content.trim()) {
      alert('Please provide script content');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiClient.put(`/api/scripts/${editingScript.id}`, {
        content: editingScript.content
      });
      
      if (response.ok) {
        await loadScripts(); // Refresh the list
        setEditingScript(null);
        setSelectedScript(null);
        alert('Script updated successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to update script');
        alert(`Failed to update script: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error updating script:', error);
      alert('Error updating script');
    } finally {
      setLoading(false);
    }
  };

  const startEditing = (script) => {
    setEditingScript({
      id: script.id,
      name: script.name,
      content: script.script_contents || ''
    });
  };

  if (editingScript) {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Edit Script: {editingScript.name}</h3>
          <div>
            <button className="btn btn-success me-2" onClick={updateScript} disabled={loading}>
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
            <button className="btn btn-secondary me-2" onClick={() => setEditingScript(null)}>
              Cancel
            </button>
            <button className="btn btn-outline-secondary" onClick={onBack}>
              Back to Dashboard
            </button>
          </div>
        </div>
        <div className="card-body">
          <div className="mb-3">
            <label htmlFor="scriptContent" className="form-label">Script Content</label>
            <textarea
              id="scriptContent"
              className="form-control"
              rows="20"
              value={editingScript.content}
              onChange={(e) => setEditingScript({ ...editingScript, content: e.target.value })}
              style={{ fontFamily: 'monospace', fontSize: '0.9em' }}
              placeholder="Enter your script content here..."
            />
          </div>
        </div>
      </div>
    );
  }

  if (selectedScript) {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Script Details</h3>
          <div>
            <button className="btn btn-warning me-2" onClick={() => startEditing(selectedScript)}>
              Edit Script
            </button>
            <button className="btn btn-secondary me-2" onClick={() => setSelectedScript(null)}>
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
              <p><strong>Name:</strong> {selectedScript.name}</p>
              <p><strong>Category:</strong> {selectedScript.category}</p>
              <p><strong>Info:</strong> {selectedScript.info || 'N/A'}</p>
              <p><strong>Notes:</strong> {selectedScript.notes || 'N/A'}</p>
              <p><strong>Priority:</strong> {selectedScript.priority}</p>
            </div>
            <div className="col-md-6">
              <h5>Parameters</h5>
              {selectedScript.parameters && selectedScript.parameters.length > 0 ? (
                <ul className="list-group list-group-flush">
                  {selectedScript.parameters.map((param, index) => (
                    <li key={index} className="list-group-item">
                      <strong>Parameter {param.parameter_number}:</strong> {param.parameter_value}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">No parameters defined</p>
              )}
            </div>
          </div>
          
          <div className="mt-4">
            <h5>Script Contents</h5>
            <pre className="bg-light p-3 rounded" style={{ fontSize: '0.9em', maxHeight: '400px', overflowY: 'auto' }}>
              {selectedScript.script_contents || 'No script content available'}
            </pre>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h3 className="mb-0">Script Management</h3>
        <div>
          <button className="btn btn-success me-2" onClick={() => setShowCreateModal(true)}>
            Create New Script
          </button>
          <button className="btn btn-primary me-2" onClick={loadScripts} disabled={loading}>
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
          <button className="btn btn-outline-secondary" onClick={onBack}>
            Back to Dashboard
          </button>
        </div>
      </div>
      
      <div className="card-body">
        {loading && scripts.length === 0 ? (
          <div className="text-center">
            <div className="spinner-border" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-2">Loading scripts...</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table table-striped">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {scripts.map((script) => (
                  <tr key={script.id}>
                    <td>{script.id}</td>
                    <td>{script.name}</td>
                    <td>{script.category || 'N/A'}</td>
                    <td>{script.priority || 'N/A'}</td>
                    <td>
                      <button 
                        className="btn btn-sm btn-outline-primary me-2"
                        onClick={() => getScriptDetails(script.id)}
                        disabled={loading}
                      >
                        View Details
                      </button>
                      <button 
                        className="btn btn-sm btn-outline-danger"
                        onClick={() => deleteScript(script.id, script.name)}
                        disabled={loading}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {scripts.length === 0 && !loading && (
          <div className="alert alert-info">
            No scripts found.
          </div>
        )}
      </div>

      {/* Create Script Modal */}
      {showCreateModal && (
        <>
          <div className="modal-backdrop fade show"></div>
          <div className="modal fade show" style={{ display: 'block', zIndex: 1055 }} tabIndex="-1">
            <div className="modal-dialog modal-lg">
              <div className="modal-content">
                <div className="modal-header">
                  <h5 className="modal-title">Create New Script</h5>
                  <button 
                    type="button" 
                    className="btn-close"
                    onClick={() => {
                      setShowCreateModal(false);
                      setNewScript({ name: '', content: '' });
                    }}
                  ></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label htmlFor="scriptName" className="form-label">Script Name</label>
                    <input
                      type="text"
                      id="scriptName"
                      className="form-control"
                      value={newScript.name}
                      onChange={(e) => setNewScript({ ...newScript, name: e.target.value })}
                      placeholder="Enter script name"
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="scriptContent" className="form-label">Script Content</label>
                    <textarea
                      id="scriptContent"
                      className="form-control"
                      rows="15"
                      value={newScript.content}
                      onChange={(e) => setNewScript({ ...newScript, content: e.target.value })}
                      style={{ fontFamily: 'monospace', fontSize: '0.9em' }}
                      placeholder="#!/bin/bash&#10;&#10;# Enter your script content here..."
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button 
                    type="button" 
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowCreateModal(false);
                      setNewScript({ name: '', content: '' });
                    }}
                  >
                    Cancel
                  </button>
                  <button 
                    type="button" 
                    className="btn btn-primary"
                    onClick={createScript}
                    disabled={loading || !newScript.name.trim() || !newScript.content.trim()}
                  >
                    {loading ? 'Creating...' : 'Create Script'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ScriptManager;
