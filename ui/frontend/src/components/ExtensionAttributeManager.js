import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { prism } from 'react-syntax-highlighter/dist/esm/styles/prism';
import apiClient from '../utils/apiClient';

const ExtensionAttributeManager = ({ sessionId, onBack }) => {
  const [extensionAttributes, setExtensionAttributes] = useState([]);
  const [selectedAttribute, setSelectedAttribute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('list'); // 'list', 'details', 'create', 'update'
  const [xmlContent, setXmlContent] = useState('');
  const [updateId, setUpdateId] = useState('');

  // Template XML content from the actual template file
  const templateXml = `<computer_extension_attribute>
    <name>Eve Test</name>
    <description>Creates /tmp/test.txt on the client</description>
    <data_type>String</data_type>
    <input_type>
        <type>script</type>
        <platform>Mac</platform>
        <script>#!/bin/bash
touch /tmp/test.txt
echo "&lt;result&gt;Created /tmp/test.txt&lt;/result&gt;"</script> <!-- Must escape <> characters -->
    </input_type>
    <inventory_display>General</inventory_display>
    <enabled>true</enabled>
</computer_extension_attribute>`;

  useEffect(() => {
    apiClient.setSession(sessionId);
    loadExtensionAttributes();
    // Pre-populate the XML content with the template when component mounts
    setXmlContent(templateXml);
  }, [sessionId, templateXml]);

  const loadExtensionAttributes = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get('/api/extension-attributes');
      
      if (response.ok) {
        const data = await response.json();
        setExtensionAttributes(data.computer_extension_attributes || data.extension_attributes || []);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load extension attributes');
      }
    } catch (error) {
      console.error('Error loading extension attributes:', error);
      setError('Network error while loading extension attributes');
    } finally {
      setLoading(false);
    }
  };

  const getAttributeDetails = async (id) => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get(`/api/extension-attributes/${id}`);
      
      if (response.ok) {
        const data = await response.json();
        setSelectedAttribute(data);
        setActiveTab('details');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to get extension attribute details');
      }
    } catch (error) {
      console.error('Error getting extension attribute details:', error);
      setError('Network error while getting extension attribute details');
    } finally {
      setLoading(false);
    }
  };

  const createExtensionAttribute = async () => {
    if (!xmlContent.trim()) {
      setError('XML content is required');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiClient.post('/api/extension-attributes', {
        xml_content: xmlContent
      });
      
      if (response.ok) {
        alert('Extension attribute created successfully!');
        setXmlContent(templateXml);
        setActiveTab('list');
        loadExtensionAttributes();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create extension attribute');
      }
    } catch (error) {
      console.error('Error creating extension attribute:', error);
      setError('Network error while creating extension attribute');
    } finally {
      setLoading(false);
    }
  };

  const updateExtensionAttribute = async () => {
    if (!updateId.trim() || !xmlContent.trim()) {
      setError('Both ID and XML content are required');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiClient.put(`/api/extension-attributes/${updateId}`, {
        xml_content: xmlContent
      });
      
      if (response.ok) {
        alert('Extension attribute updated successfully!');
        setXmlContent(templateXml);
        setUpdateId('');
        setActiveTab('list');
        loadExtensionAttributes();
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to update extension attribute');
      }
    } catch (error) {
      console.error('Error updating extension attribute:', error);
      setError('Network error while updating extension attribute');
    } finally {
      setLoading(false);
    }
  };

  const deleteExtensionAttribute = async (id) => {
    if (!window.confirm('Are you sure you want to delete this extension attribute? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiClient.delete(`/api/extension-attributes/${id}`);
      
      if (response.ok) {
        alert('Extension attribute deleted successfully!');
        loadExtensionAttributes();
        if (selectedAttribute && selectedAttribute.computer_extension_attribute?.id === id) {
          setSelectedAttribute(null);
          setActiveTab('list');
        }
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to delete extension attribute');
      }
    } catch (error) {
      console.error('Error deleting extension attribute:', error);
      setError('Network error while deleting extension attribute');
    } finally {
      setLoading(false);
    }
  };

  const renderTabNavigation = () => (
    <ul className="nav nav-tabs mb-3">
      <li className="nav-item">
        <button 
          className={`nav-link ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          Extension Attributes List
        </button>
      </li>
      {selectedAttribute && (
        <li className="nav-item">
          <button 
            className={`nav-link ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => setActiveTab('details')}
          >
            Details
          </button>
        </li>
      )}
      <li className="nav-item">
        <button 
          className={`nav-link ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          Create New
        </button>
      </li>
      <li className="nav-item">
        <button 
          className={`nav-link ${activeTab === 'update' ? 'active' : ''}`}
          onClick={() => setActiveTab('update')}
        >
          Update Existing
        </button>
      </li>
    </ul>
  );

  const renderListView = () => (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5>Extension Attributes ({extensionAttributes.length})</h5>
        <button 
          className="btn btn-primary" 
          onClick={loadExtensionAttributes}
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {extensionAttributes.length > 0 ? (
        <div className="table-responsive">
          <table className="table table-striped">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Data Type</th>
                <th>Input Type</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {extensionAttributes.map((attr) => (
                <tr key={attr.id}>
                  <td>{attr.id}</td>
                  <td>{attr.name}</td>
                  <td>
                    <span className="badge bg-info">{attr.data_type || 'N/A'}</span>
                  </td>
                  <td>{attr.input_type?.type || 'N/A'}</td>
                  <td>
                    <button 
                      className="btn btn-sm btn-outline-primary me-2"
                      onClick={() => getAttributeDetails(attr.id)}
                      disabled={loading}
                    >
                      View Details
                    </button>
                    <button 
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => deleteExtensionAttribute(attr.id)}
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
      ) : (
        <div className="alert alert-info">
          No extension attributes found. Create a new one to get started.
        </div>
      )}
    </div>
  );

  const renderDetailsView = () => {
    if (!selectedAttribute) return null;

    const attr = selectedAttribute.computer_extension_attribute || selectedAttribute;
    
    return (
      <div>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h5>Extension Attribute Details</h5>
          <button 
            className="btn btn-outline-secondary"
            onClick={() => setActiveTab('list')}
          >
            Back to List
          </button>
        </div>

        <div className="row">
          <div className="col-md-6">
            <div className="card">
              <div className="card-header">
                <h6 className="mb-0">Basic Information</h6>
              </div>
              <div className="card-body">
                <p><strong>ID:</strong> {attr.id}</p>
                <p><strong>Name:</strong> {attr.name}</p>
                <p><strong>Description:</strong> {attr.description || 'N/A'}</p>
                <p><strong>Data Type:</strong> <span className="badge bg-info">{attr.data_type}</span></p>
                <p><strong>Inventory Display:</strong> {attr.inventory_display}</p>
                <p><strong>Enabled:</strong> {attr.enabled ? 'Yes' : 'No'}</p>
              </div>
            </div>
          </div>
          
          <div className="col-md-6">
            <div className="card">
              <div className="card-header">
                <h6 className="mb-0">Input Configuration</h6>
              </div>
              <div className="card-body">
                <p><strong>Input Type:</strong> {attr.input_type?.type}</p>
                <p><strong>Platform:</strong> {attr.input_type?.platform || 'N/A'}</p>
                {attr.input_type?.popup_choices && (
                  <div>
                    <strong>Popup Choices:</strong>
                    <ul className="mt-2">
                      {attr.input_type.popup_choices.map((choice, index) => (
                        <li key={index}>{choice}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {attr.input_type?.script && (
                  <div className="mt-2">
                    <strong>Script:</strong>
                    <SyntaxHighlighter
                      language="bash"
                      style={prism}
                      customStyle={{ fontSize: '0.8rem', maxHeight: '200px' }}
                    >
                      {attr.input_type.script}
                    </SyntaxHighlighter>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4">
          <div className="card">
            <div className="card-header">
              <h6 className="mb-0">Full JSON Data</h6>
            </div>
            <div className="card-body">
              <SyntaxHighlighter
                language="json"
                style={prism}
                customStyle={{ fontSize: '0.8rem', maxHeight: '400px' }}
              >
                {JSON.stringify(selectedAttribute, null, 2)}
              </SyntaxHighlighter>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderCreateView = () => (
    <div>
      <h5>Create New Extension Attribute</h5>
      <p className="text-muted">Provide XML content to create a new computer extension attribute.</p>
      
      <div className="mb-3">
        <label className="form-label">XML Content</label>
        <textarea
          className="form-control"
          rows="20"
          value={xmlContent}
          onChange={(e) => setXmlContent(e.target.value)}
          placeholder="Enter XML content for the extension attribute..."
          style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
        />
      </div>
      <div className="d-flex gap-2">
        <button 
          className="btn btn-primary"
          onClick={createExtensionAttribute}
          disabled={loading || !xmlContent.trim()}
        >
          {loading ? 'Creating...' : 'Create Extension Attribute'}
        </button>
        <button 
          className="btn btn-outline-secondary"
          onClick={() => setXmlContent(templateXml)}
        >
          Reset to Template
        </button>
      </div>
    </div>
  );

  const renderUpdateView = () => (
    <div>
      <h5>Update Extension Attribute</h5>
      <p className="text-muted">Provide the ID and XML content to update an existing extension attribute.</p>
      
      <div className="row">
        <div className="col-md-6">
          <div className="mb-3">
            <label className="form-label">Extension Attribute ID</label>
            <input
              type="text"
              className="form-control"
              value={updateId}
              onChange={(e) => setUpdateId(e.target.value)}
              placeholder="Enter the ID of the extension attribute to update"
            />
          </div>
          <div className="mb-3">
            <label className="form-label">Updated XML Content</label>
            <textarea
              className="form-control"
              rows="12"
              value={xmlContent}
              onChange={(e) => setXmlContent(e.target.value)}
              placeholder="Enter updated XML content..."
              style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
            />
          </div>
          <div className="d-flex gap-2">
            <button 
              className="btn btn-warning"
              onClick={updateExtensionAttribute}
              disabled={loading || !updateId.trim() || !xmlContent.trim()}
            >
              {loading ? 'Updating...' : 'Update Extension Attribute'}
            </button>
            <button 
              className="btn btn-outline-secondary"
              onClick={() => setXmlContent(templateXml)}
            >
              Reset to Template
            </button>
          </div>
        </div>
        
        <div className="col-md-6">
          <div className="alert alert-warning">
            <strong>Warning:</strong> Updating an extension attribute will modify its configuration. 
            Make sure you have the correct ID and valid XML content.
          </div>
          
          {extensionAttributes.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h6 className="mb-0">Available Extension Attributes</h6>
              </div>
              <div className="card-body">
                <div className="table-responsive" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                  <table className="table table-sm">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {extensionAttributes.map((attr) => (
                        <tr key={attr.id}>
                          <td>{attr.id}</td>
                          <td>{attr.name}</td>
                          <td>
                            <button 
                              className="btn btn-sm btn-outline-primary"
                              onClick={() => setUpdateId(attr.id.toString())}
                            >
                              Select
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h3 className="mb-0">Extension Attribute Management</h3>
        <button className="btn btn-outline-secondary" onClick={onBack}>
          Back to Dashboard
        </button>
      </div>
      
      <div className="card-body">
        {error && (
          <div className="alert alert-danger" role="alert">
            {error}
          </div>
        )}

        {renderTabNavigation()}
        
        {activeTab === 'list' && renderListView()}
        {activeTab === 'details' && renderDetailsView()}
        {activeTab === 'create' && renderCreateView()}
        {activeTab === 'update' && renderUpdateView()}
      </div>
    </div>
  );
};

export default ExtensionAttributeManager;
