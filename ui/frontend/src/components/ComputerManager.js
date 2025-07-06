import React, { useState } from 'react';

const ComputerManager = ({ sessionId, onBack }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [computers, setComputers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedComputer, setSelectedComputer] = useState(null);

  const searchComputers = async () => {
    if (!searchTerm.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/computers/search/${encodeURIComponent(searchTerm)}`, {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setComputers(data.computers || []);
      } else {
        console.error('Failed to search computers');
      }
    } catch (error) {
      console.error('Error searching computers:', error);
    } finally {
      setLoading(false);
    }
  };

  const getComputerDetails = async (id) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/computers/id/${id}`, {
        headers: {
          'X-Session-ID': sessionId,
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedComputer(data.computer || data);
      } else {
        console.error('Failed to get computer details');
      }
    } catch (error) {
      console.error('Error getting computer details:', error);
    } finally {
      setLoading(false);
    }
  };

  if (selectedComputer) {
    return (
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h3 className="mb-0">Computer Details</h3>
          <div>
            <button className="btn btn-secondary me-2" onClick={() => setSelectedComputer(null)}>
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
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => getComputerDetails(computer.id)}
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

        {computers.length === 0 && searchTerm && !loading && (
          <div className="alert alert-info">
            No computers found matching "{searchTerm}". Try a different search term.
          </div>
        )}
      </div>
    </div>
  );
};

export default ComputerManager;
