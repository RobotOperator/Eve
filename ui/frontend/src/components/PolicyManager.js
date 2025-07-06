import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { prism } from 'react-syntax-highlighter/dist/esm/styles/prism';
import xmlFormatter from 'xml-formatter';

const PolicyManager = ({ sessionId, onBack }) => {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [viewMode, setViewMode] = useState('list'); // 'list', 'details', 'xml', 'create', 'edit'
  const [policyXml, setPolicyXml] = useState('');
  const [editingXml, setEditingXml] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  // Default policy template
  const defaultPolicyTemplate = `<policy>
    <general>   
        <name>New Policy</name>
        <enabled>true</enabled>
        <target_drive>/</target_drive>
        <trigger>EVENT</trigger>
        <trigger_checkin>true</trigger_checkin>
        <frequency>Once per computer</frequency>
    </general>
    <scope>
        <computers>
        </computers>
    </scope>
    <scripts>
    </scripts>
</policy>`;

  useEffect(() => {
    loadPolicies();
  }, []);

  // Function to format XML with proper indentation
  const formatXml = (xml) => {
    if (!xml) return '';
    
    try {
      return xmlFormatter(xml, {
        indentation: '  ',
        filter: (node) => node.type !== 'Comment',
        collapseContent: true,
        lineSeparator: '\n'
      });
    } catch (error) {
      console.error('Error formatting XML:', error);
      return xml; // Return original if formatting fails
    }
  };

  const loadPolicies = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/policies', {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPolicies(data.policies || []);
      } else {
        console.error('Failed to load policies');
      }
    } catch (error) {
      console.error('Error loading policies:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPolicyDetails = async (id) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/policies/${id}`, {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedPolicy(data.policy || data);
      } else {
        console.error('Failed to get policy details');
      }
    } catch (error) {
      console.error('Error getting policy details:', error);
    } finally {
      setLoading(false);
    }
  };

  const deletePolicy = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete policy "${name}"?`)) {
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`/api/policies/${id}`, {
        method: 'DELETE',
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        await loadPolicies(); // Refresh the list
        alert('Policy deleted successfully');
      } else {
        alert('Failed to delete policy');
      }
    } catch (error) {
      console.error('Error deleting policy:', error);
      alert('Error deleting policy');
    } finally {
      setLoading(false);
    }
  };

  const getPolicyXml = async (id) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/policies/${id}/xml`, {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPolicyXml(data.xml);
        setEditingXml(data.xml);
        setViewMode('xml');
      } else {
        console.error('Failed to get policy XML');
        alert('Failed to get policy XML');
      }
    } catch (error) {
      console.error('Error getting policy XML:', error);
      alert('Error getting policy XML');
    } finally {
      setLoading(false);
    }
  };

  const createPolicy = async () => {
    setIsCreating(true);
    try {
      const response = await fetch('/api/policies', {
        method: 'POST',
        headers: {
          'X-Session-ID': sessionId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ xml: editingXml })
      });
      
      if (response.ok) {
        await loadPolicies(); // Refresh the list
        setViewMode('list');
        setEditingXml('');
        alert('Policy created successfully');
      } else {
        const error = await response.json();
        alert(`Failed to create policy: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating policy:', error);
      alert('Error creating policy');
    } finally {
      setIsCreating(false);
    }
  };

  const updatePolicy = async (id) => {
    setIsUpdating(true);
    try {
      const response = await fetch(`/api/policies/${id}`, {
        method: 'PUT',
        headers: {
          'X-Session-ID': sessionId,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ xml: editingXml })
      });
      
      if (response.ok) {
        await loadPolicies(); // Refresh the list
        setPolicyXml(editingXml); // Update displayed XML
        alert('Policy updated successfully');
      } else {
        const error = await response.json();
        alert(`Failed to update policy: ${error.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error updating policy:', error);
      alert('Error updating policy');
    } finally {
      setIsUpdating(false);
    }
  };

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const response = await fetch('/api/policy-templates', {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      } else {
        console.error('Failed to load templates');
        alert('Failed to load policy templates');
      }
    } catch (error) {
      console.error('Error loading templates:', error);
      alert('Error loading policy templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const startCreatePolicyWithTemplate = () => {
    loadTemplates();
    setShowTemplateModal(true);
  };

  const selectTemplate = (template) => {
    setEditingXml(template.content);
    setShowTemplateModal(false);
    setViewMode('create');
  };

  const createPolicyFromScratch = () => {
    setEditingXml(defaultPolicyTemplate);
    setShowTemplateModal(false);
    setViewMode('create');
  };

  const startEditPolicy = () => {
    setViewMode('edit');
  };

  const cancelEdit = () => {
    setEditingXml(policyXml); // Reset to original
    setViewMode('xml');
  };

  // Template selection modal
  const TemplateModal = () => (
    <div className={`modal fade ${showTemplateModal ? 'show' : ''}`} 
         style={{ display: showTemplateModal ? 'block' : 'none' }}
         tabIndex="-1">
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Select Policy Template</h5>
            <button type="button" className="btn-close" onClick={() => setShowTemplateModal(false)}></button>
          </div>
          <div className="modal-body">
            <p className="text-muted mb-4">Choose a template to start with, or create a blank policy from scratch.</p>
            
            {loadingTemplates ? (
              <div className="text-center">
                <div className="spinner-border" role="status">
                  <span className="visually-hidden">Loading templates...</span>
                </div>
                <p className="mt-2">Loading templates...</p>
              </div>
            ) : (
              <div className="row g-3">
                {/* Blank template option */}
                <div className="col-md-6">
                  <div 
                    className="card template-card h-100" 
                    onClick={createPolicyFromScratch}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="card-body text-center">
                      <div className="display-4 mb-3">📝</div>
                      <h5 className="card-title">Blank Policy</h5>
                      <p className="card-text text-muted">Start with a minimal policy template</p>
                    </div>
                  </div>
                </div>

                {/* Template options */}
                {templates.map((template) => (
                  <div key={template.id} className="col-md-6">
                    <div 
                      className="card template-card h-100" 
                      onClick={() => selectTemplate(template)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="card-body text-center">
                        <div className="display-4 mb-3">{template.icon}</div>
                        <h5 className="card-title">{template.name}</h5>
                        <p className="card-text text-muted">{template.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={() => setShowTemplateModal(false)}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // XML view with syntax highlighting (basic)
  if (viewMode === 'xml') {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Policy XML - {selectedPolicy?.general?.name}</h3>
          <div>
            <button className="btn btn-primary me-2" onClick={startEditPolicy}>
              Edit XML
            </button>
            <button className="btn btn-secondary me-2" onClick={() => setViewMode('details')}>
              View Details
            </button>
            <button className="btn btn-secondary me-2" onClick={() => setViewMode('list')}>
              Back to List
            </button>
            <button className="btn btn-outline-secondary" onClick={onBack}>
              Back to Dashboard
            </button>
          </div>
        </div>
        <div className="card-body">
          <SyntaxHighlighter
            language="xml"
            style={prism}
            className="xml-viewer"
            customStyle={{
              maxHeight: '70vh',
              fontSize: '0.875rem',
              lineHeight: '1.4',
              borderRadius: '0.375rem',
              backgroundColor: '#ffffff',
              border: '1px solid #dee2e6',
              padding: '1rem',
              margin: 0
            }}
            showLineNumbers={true}
            lineNumberStyle={{
              color: '#6c757d',
              backgroundColor: '#f8f9fa',
              paddingRight: '1rem',
              textAlign: 'right',
              borderRight: '1px solid #dee2e6',
              marginRight: '1rem'
            }}
          >
            {formatXml(policyXml)}
          </SyntaxHighlighter>
        </div>
      </div>
    );
  }

  // Create/Edit policy form
  if (viewMode === 'create' || viewMode === 'edit') {
    const isEdit = viewMode === 'edit';
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">{isEdit ? 'Edit Policy XML' : 'Create New Policy'}</h3>
          <div>
            {isEdit && (
              <button className="btn btn-secondary me-2" onClick={cancelEdit}>
                Cancel
              </button>
            )}
            <button 
              className="btn btn-secondary me-2" 
              onClick={() => setViewMode(isEdit ? 'xml' : 'list')}
            >
              {isEdit ? 'Back to View' : 'Back to List'}
            </button>
            <button className="btn btn-outline-secondary" onClick={onBack}>
              Back to Dashboard
            </button>
          </div>
        </div>
        <div className="card-body">
          <div className="mb-3">
            <label className="form-label">Policy XML:</label>
            <textarea
              className="form-control"
              value={editingXml}
              onChange={(e) => setEditingXml(e.target.value)}
              rows={20}
              style={{ 
                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                fontSize: '0.875rem'
              }}
              placeholder="Enter policy XML here..."
            />
          </div>
          <div className="d-flex gap-2">
            <button 
              className="btn btn-success"
              onClick={() => isEdit ? updatePolicy(selectedPolicy.general.id) : createPolicy()}
              disabled={isEdit ? isUpdating : isCreating}
            >
              {isEdit 
                ? (isUpdating ? 'Updating...' : 'Update Policy') 
                : (isCreating ? 'Creating...' : 'Create Policy')
              }
            </button>
            <button 
              className="btn btn-secondary"
              onClick={() => setViewMode(isEdit ? 'xml' : 'list')}
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }
  // Policy details view
  if (viewMode === 'details' && selectedPolicy) {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Policy Details</h3>
          <div>
            <button className="btn btn-primary me-2" onClick={() => getPolicyXml(selectedPolicy.general.id)}>
              View XML
            </button>
            <button className="btn btn-secondary me-2" onClick={() => setViewMode('list')}>
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
              <p><strong>Name:</strong> {selectedPolicy.general?.name}</p>
              <p><strong>Category:</strong> {selectedPolicy.general?.category?.name}</p>
              <p><strong>Enabled:</strong> {selectedPolicy.general?.enabled ? 'Yes' : 'No'}</p>
              <p><strong>Trigger:</strong> {selectedPolicy.general?.trigger}</p>
              <p><strong>Frequency:</strong> {selectedPolicy.general?.frequency}</p>
            </div>
            <div className="col-md-6">
              <h5>Scope</h5>
              <p><strong>Target Computers:</strong> {selectedPolicy.scope?.computers?.length || 0}</p>
              <p><strong>Target Groups:</strong> {selectedPolicy.scope?.computer_groups?.length || 0}</p>
              <p><strong>Limitations:</strong> {selectedPolicy.scope?.limitations ? 'Yes' : 'No'}</p>
              <p><strong>Exclusions:</strong> {selectedPolicy.scope?.exclusions ? 'Yes' : 'No'}</p>
            </div>
          </div>
          
          {selectedPolicy.scripts?.length > 0 && (
            <div className="mt-4">
              <h5>Scripts</h5>
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Priority</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedPolicy.scripts.map((script, index) => (
                      <tr key={index}>
                        <td>{script.name}</td>
                        <td>{script.priority}</td>
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

  // Main policy list view
  return (
    <>
      <TemplateModal />
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Policy Management</h3>
          <div>
            <button className="btn btn-success me-2" onClick={startCreatePolicyWithTemplate}>
              Create Policy
            </button>
            <button className="btn btn-primary me-2" onClick={loadPolicies} disabled={loading}>
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
            <button className="btn btn-outline-secondary" onClick={onBack}>
              Back to Dashboard
            </button>
          </div>
        </div>
        
        <div className="card-body">
          {loading && policies.length === 0 ? (
            <div className="text-center">
              <div className="spinner-border" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-2">Loading policies...</p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-striped">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Category</th>
                    <th>Enabled</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.map((policy) => (
                    <tr key={policy.id}>
                      <td>{policy.id}</td>
                      <td>{policy.name}</td>
                      <td>{policy.category || 'N/A'}</td>
                      <td>
                        <span className={`badge ${policy.enabled ? 'bg-success' : 'bg-secondary'}`}>
                          {policy.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn btn-sm btn-outline-primary me-2"
                          onClick={() => {
                            getPolicyDetails(policy.id);
                            setViewMode('details');
                          }}
                          disabled={loading}
                        >
                          View Details
                        </button>
                        <button 
                          className="btn btn-sm btn-outline-info me-2"
                          onClick={() => {
                            setSelectedPolicy({ general: { id: policy.id, name: policy.name } });
                            getPolicyXml(policy.id);
                          }}
                          disabled={loading}
                        >
                          View XML
                        </button>
                        <button 
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => deletePolicy(policy.id, policy.name)}
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

          {policies.length === 0 && !loading && (
            <div className="alert alert-info">
              No policies found.
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default PolicyManager;
