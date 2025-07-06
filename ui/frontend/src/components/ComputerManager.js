import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { prism } from 'react-syntax-highlighter/dist/esm/styles/prism';
import apiClient from '../utils/apiClient';

const ComputerManager = ({ sessionId, onBack }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [computers, setComputers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedComputer, setSelectedComputer] = useState(null);
  const [viewMode, setViewMode] = useState('details'); // 'details' or 'json'
  const [error, setError] = useState('');

  useEffect(() => {
    apiClient.setSession(sessionId);
  }, [sessionId]);

  // Function to format JSON with proper indentation
  const formatJson = (obj) => {
    if (!obj) return '';
    try {
      return JSON.stringify(obj, null, 2);
    } catch (error) {
      console.error('Error formatting JSON:', error);
      return JSON.stringify(obj);
    }
  };

  const searchComputers = async () => {
    if (!searchTerm.trim()) return;
    
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get(`/api/computers/search/${encodeURIComponent(searchTerm)}`);
      
      if (response.ok) {
        const data = await response.json();
        setComputers(data.computers || []);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to search computers');
      }
    } catch (error) {
      console.error('Error searching computers:', error);
      setError('Network error while searching computers');
    } finally {
      setLoading(false);
    }
  };

  const getComputerDetails = async (id, targetViewMode = 'details') => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get(`/api/computers/id/${id}`);
      
      if (response.ok) {
        const data = await response.json();
        setSelectedComputer(data.computer || data);
        // Set the target view mode
        setViewMode(targetViewMode);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to get computer details');
      }
    } catch (error) {
      console.error('Error getting computer details:', error);
    } finally {
      setLoading(false);
    }
  };

  // JSON view for computer data
  if (selectedComputer && viewMode === 'json') {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Computer JSON - {selectedComputer.general?.name}</h3>
          <div>
            <button className="btn btn-primary me-2" onClick={() => setViewMode('details')}>
              View Details
            </button>
            <button className="btn btn-secondary me-2" onClick={() => {
              setSelectedComputer(null);
              setViewMode('details');
            }}>
              Back to List
            </button>
            <button className="btn btn-outline-secondary" onClick={onBack}>
              Back to Dashboard
            </button>
          </div>
        </div>
        <div className="card-body">
          <SyntaxHighlighter
            language="json"
            style={prism}
            className="json-viewer"
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
            {formatJson(selectedComputer)}
          </SyntaxHighlighter>
        </div>
      </div>
    );
  }

  // Details view for computer data
  if (selectedComputer) {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Computer Details</h3>
          <div>
            <button className="btn btn-primary me-2" onClick={() => setViewMode('json')}>
              View JSON
            </button>
            <button className="btn btn-secondary me-2" onClick={() => {
              setSelectedComputer(null);
              setViewMode('details');
            }}>
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
              <p><strong>Name:</strong> {selectedComputer.general?.name}</p>
              <p><strong>Serial Number:</strong> {selectedComputer.general?.serial_number}</p>
              <p><strong>UDID:</strong> {selectedComputer.general?.udid}</p>
              <p><strong>Model:</strong> {selectedComputer.hardware?.model}</p>
              <p><strong>OS Version:</strong> {selectedComputer.hardware?.os_version}</p>
              <p><strong>Last Check-in:</strong> {selectedComputer.general?.last_contact_time}</p>
            </div>
            <div className="col-md-6">
              <h5>Hardware Information</h5>
              <p><strong>Processor:</strong> {selectedComputer.hardware?.processor_type}</p>
              <p><strong>RAM:</strong> {selectedComputer.hardware?.total_ram} MB</p>
              <p><strong>Storage:</strong> {selectedComputer.hardware?.storage?.[0]?.size} MB</p>
              <p><strong>MAC Address:</strong> {selectedComputer.general?.mac_address}</p>
              <p><strong>IP Address:</strong> {selectedComputer.general?.ip_address}</p>
            </div>
          </div>
          
          {/* Additional sections for more detailed information */}
          {selectedComputer.location && (
            <div className="mt-4">
              <h5>Location Information</h5>
              <div className="row">
                <div className="col-md-6">
                  <p><strong>Building:</strong> {selectedComputer.location.building}</p>
                  <p><strong>Department:</strong> {selectedComputer.location.department}</p>
                  <p><strong>Room:</strong> {selectedComputer.location.room}</p>
                </div>
                <div className="col-md-6">
                  <p><strong>Position:</strong> {selectedComputer.location.position}</p>
                  <p><strong>Phone:</strong> {selectedComputer.location.phone}</p>
                  <p><strong>Email:</strong> {selectedComputer.location.email_address}</p>
                </div>
              </div>
            </div>
          )}

          {selectedComputer.extension_attributes && selectedComputer.extension_attributes.length > 0 && (
            <div className="mt-4">
              <h5>Extension Attributes</h5>
              <div className="table-responsive">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedComputer.extension_attributes.map((attr, index) => (
                      <tr key={index}>
                        <td>{attr.name}</td>
                        <td>{attr.value || 'N/A'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {selectedComputer.software && selectedComputer.software.applications && selectedComputer.software.applications.length > 0 && (
            <div className="mt-4">
              <h5>Applications ({selectedComputer.software.applications.length})</h5>
              <div className="table-responsive" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Version</th>
                      <th>Path</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedComputer.software.applications.slice(0, 50).map((app, index) => (
                      <tr key={index}>
                        <td>{app.name}</td>
                        <td>{app.version}</td>
                        <td><small>{app.path}</small></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {selectedComputer.software.applications.length > 50 && (
                  <p className="text-muted mt-2">
                    Showing first 50 applications. View JSON for complete list.
                  </p>
                )}
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
        <h3 className="mb-0">Computer Management</h3>
        <button className="btn btn-outline-secondary" onClick={onBack}>
          Back to Dashboard
        </button>
      </div>
      
      <div className="card-body">
        <div className="row mb-4">
          <div className="col-md-8">
            <input
              type="text"
              className="form-control"
              placeholder="Search for computers by name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchComputers()}
              autoComplete="off"
              autoCorrect="off"
              autoCapitalize="off"
              spellCheck="false"
            />
          </div>
          <div className="col-md-4">
            <button 
              className="btn btn-primary w-100" 
              onClick={searchComputers}
              disabled={loading || !searchTerm.trim()}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        {computers.length > 0 && (
          <div className="table-responsive">
            <table className="table table-striped">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Serial Number</th>
                  <th>Model</th>
                  <th>OS Version</th>
                  <th>Last Check-in</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {computers.map((computer) => (
                  <tr key={computer.id}>
                    <td>{computer.name}</td>
                    <td>{computer.serial_number}</td>
                    <td>{computer.model}</td>
                    <td>{computer.os_version}</td>
                    <td>{computer.last_contact_time}</td>
                    <td>
                      <button 
                        className="btn btn-sm btn-outline-primary me-2"
                        onClick={() => getComputerDetails(computer.id, 'details')}
                      >
                        View Details
                      </button>
                      <button 
                        className="btn btn-sm btn-outline-info"
                        onClick={() => getComputerDetails(computer.id, 'json')}
                      >
                        View JSON
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComputerManager;
