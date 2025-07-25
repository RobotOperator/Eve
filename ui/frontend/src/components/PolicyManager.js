import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { prism, vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import xmlFormatter from 'xml-formatter';
import apiClient from '../utils/apiClient';

// Separate HelperPane component to prevent re-creation on every render
const HelperPane = ({ 
  showHelperPane, 
  helperContext, 
  helperData, 
  helperLoading, 
  helperSearch, 
  onSearchChange, 
  onClose, 
  onInsertValue 
}) => {
  const searchInputRef = useRef(null);

  if (!showHelperPane || !helperContext) return null;

  const getContextTitle = () => {
    switch (helperContext) {
      case 'computers': return 'Computer Lookup';
      case 'scripts': return 'Script Lookup';
      case 'users': return 'User Lookup';
      case 'groups': return 'Group Lookup';
      default: return 'Lookup';
    }
  };

  const getContextDescription = () => {
    switch (helperContext) {
      case 'computers': return 'Click a computer to insert its ID and name into the policy';
      case 'scripts': return 'Click a script to insert its ID and name into the policy';
      case 'users': return 'Click a user to insert their ID and name into the policy';
      case 'groups': return 'Click a group to insert its ID and name into the policy';
      default: return '';
    }
  };

  const filteredData = helperData.filter(item => {
    if (!helperSearch) return true;
    const searchLower = helperSearch.toLowerCase();
    return (item.name && item.name.toLowerCase().includes(searchLower)) ||
           (item.serial_number && item.serial_number.toLowerCase().includes(searchLower)) ||
           (item.id && item.id.toString().includes(searchLower));
  });

  return (
    <div 
      className="helper-pane-floating"
      style={{
        position: 'fixed',
        top: '120px',
        right: '20px',
        width: '350px',
        maxHeight: '70vh',
        zIndex: 1000,
        backgroundColor: 'var(--bs-body-bg)',
        border: '1px solid var(--bs-border-color)',
        borderRadius: '0.5rem',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
      }}
    >
      <div className="card-header d-flex justify-content-between align-items-center p-2">
        <div>
          <h6 className="mb-0 text-sm">{getContextTitle()}</h6>
          <small className="text-muted">{getContextDescription()}</small>
        </div>
        <button 
          className="btn btn-sm btn-outline-secondary"
          onClick={onClose}
          style={{ padding: '2px 6px', fontSize: '12px' }}
        >
          ✕
        </button>
      </div>
      <div className="card-body p-2">
        <div className="mb-2">
          <input
            ref={searchInputRef}
            type="text"
            className="form-control form-control-sm"
            placeholder={`Search ${helperContext}...`}
            value={helperSearch}
            onChange={(e) => onSearchChange(e.target.value)}
            autoComplete="off"
          />
        </div>
        
        {helperLoading ? (
          <div className="text-center p-2">
            <div className="spinner-border spinner-border-sm" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : (
          <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
            {filteredData.length > 0 ? (
              <div className="list-group list-group-flush">
                {filteredData.slice(0, 20).map((item, index) => (
                  <button
                    key={item.id || index}
                    className="list-group-item list-group-item-action p-2"
                    onClick={() => onInsertValue(item, helperContext.slice(0, -1))}
                    style={{ fontSize: '0.875rem' }}
                  >
                    <div className="d-flex justify-content-between align-items-center">
                      <div>
                        <div className="fw-bold">{item.name}</div>
                        {item.serial_number && (
                          <small className="text-muted">SN: {item.serial_number}</small>
                        )}
                        {item.category && (
                          <small className="text-muted">Category: {item.category}</small>
                        )}
                      </div>
                      <small className="text-muted">ID: {item.id}</small>
                    </div>
                  </button>
                ))}
                {filteredData.length > 20 && (
                  <div className="p-2 text-center text-muted">
                    <small>Showing first 20 results. Use search to narrow down.</small>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-muted p-2">
                <small>No {helperContext} found</small>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

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
  const [error, setError] = useState('');
  
  // Dark mode detection
  const [isDarkMode, setIsDarkMode] = useState(
    document.documentElement.getAttribute('data-bs-theme') === 'dark'
  );
  
  // Helper pane state
  const [showHelperPane, setShowHelperPane] = useState(false);
  const [helperContext, setHelperContext] = useState(null); // 'computers', 'scripts', 'users', 'groups'
  const [helperData, setHelperData] = useState([]);
  const [helperLoading, setHelperLoading] = useState(false);
  const [helperSearch, setHelperSearch] = useState('');
  const [cursorPosition, setCursorPosition] = useState(0);

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
    apiClient.setSession(sessionId);
    loadPolicies();
  }, [sessionId]);

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

  // Monitor theme changes
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const newTheme = document.documentElement.getAttribute('data-bs-theme');
      setIsDarkMode(newTheme === 'dark');
    });
    
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-bs-theme']
    });
    
    return () => observer.disconnect();
  }, []);

  const loadPolicies = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get('/api/policies');
      
      if (response.ok) {
        const data = await response.json();
        setPolicies(data.policies || []);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load policies');
      }
    } catch (error) {
      console.error('Error loading policies:', error);
      setError('Network error while loading policies');
    } finally {
      setLoading(false);
    }
  };

  const getPolicyDetails = async (id) => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get(`/api/policies/${id}`);
      
      if (response.ok) {
        const data = await response.json();
        setSelectedPolicy(data.policy || data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to get policy details');
      }
    } catch (error) {
      console.error('Error getting policy details:', error);
      setError('Network error while getting policy details');
    } finally {
      setLoading(false);
    }
  };

  const deletePolicy = async (id, name) => {
    if (!window.confirm(`Are you sure you want to delete policy "${name}"?`)) {
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiClient.delete(`/api/policies/${id}`);
      
      if (response.ok) {
        await loadPolicies(); // Refresh the list
        alert('Policy deleted successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to delete policy');
        alert('Failed to delete policy');
      }
    } catch (error) {
      console.error('Error deleting policy:', error);
      setError('Network error while deleting policy');
      alert('Error deleting policy');
    } finally {
      setLoading(false);
    }
  };

  const getPolicyXml = async (id) => {
    setLoading(true);
    setError('');
    try {
      const response = await apiClient.get(`/api/policies/${id}/xml`);
      
      if (response.ok) {
        const data = await response.json();
        setPolicyXml(data.xml);
        setEditingXml(data.xml);
        setViewMode('xml');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to get policy XML');
        alert('Failed to get policy XML');
      }
    } catch (error) {
      console.error('Error getting policy XML:', error);
      setError('Network error while getting policy XML');
      alert('Error getting policy XML');
    } finally {
      setLoading(false);
    }
  };

  const createPolicy = async () => {
    setIsCreating(true);
    setError('');
    try {
      const response = await apiClient.post('/api/policies', { xml: editingXml });
      
      if (response.ok) {
        await loadPolicies(); // Refresh the list
        setViewMode('list');
        setEditingXml('');
        alert('Policy created successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to create policy');
        alert(`Failed to create policy: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error creating policy:', error);
      setError('Network error while creating policy');
      alert('Error creating policy');
    } finally {
      setIsCreating(false);
    }
  };

  const updatePolicy = async (id) => {
    setIsUpdating(true);
    setError('');
    try {
      const response = await apiClient.put(`/api/policies/${id}`, { xml: editingXml });
      
      if (response.ok) {
        await loadPolicies(); // Refresh the list
        setPolicyXml(editingXml); // Update displayed XML
        alert('Policy updated successfully');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to update policy');
        alert(`Failed to update policy: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error updating policy:', error);
      setError('Network error while updating policy');
      alert('Error updating policy');
    } finally {
      setIsUpdating(false);
    }
  };

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    setError('');
    try {
      const response = await apiClient.get('/api/policy-templates');
      
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load templates');
        alert('Failed to load policy templates');
      }
    } catch (error) {
      console.error('Error loading templates:', error);
      setError('Network error while loading templates');
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

  // Helper pane functions
  const detectContext = (xmlContent, cursorPos) => {
    if (!xmlContent || cursorPos < 0) return null;
    
    // Get text around cursor position
    const beforeCursor = xmlContent.substring(0, cursorPos);
    const afterCursor = xmlContent.substring(cursorPos);
    
    // Find the current XML context by looking for tags
    const beforeMatch = beforeCursor.match(/<([^/>]+)>?[^<]*$/);
    const afterMatch = afterCursor.match(/^[^<]*<\/([^>]+)>/);
    
    if (beforeMatch || afterMatch) {
      const tag = beforeMatch ? beforeMatch[1] : afterMatch ? afterMatch[1] : '';
      
      // Check for computer-related contexts
      if (tag.includes('computer') || (beforeCursor.includes('<computers>') && !beforeCursor.includes('</computers>'))) {
        return 'computers';
      }
      
      // Check for script-related contexts
      if (tag.includes('script') || (beforeCursor.includes('<scripts>') && !beforeCursor.includes('</scripts>'))) {
        return 'scripts';
      }
      
      // Check for user-related contexts
      if (tag.includes('user') || (beforeCursor.includes('<users>') && !beforeCursor.includes('</users>'))) {
        return 'users';
      }
      
      // Check for group-related contexts
      if (tag.includes('group') || (beforeCursor.includes('<groups>') && !beforeCursor.includes('</groups>'))) {
        return 'groups';
      }
    }
    
    return null;
  };

  const loadHelperData = async (context, searchTerm = '') => {
    if (!context) return;
    
    setHelperLoading(true);
    try {
      let endpoint = '';
      switch (context) {
        case 'computers':
          endpoint = searchTerm ? `/api/computers/search/${encodeURIComponent(searchTerm)}` : '/api/computers';
          break;
        case 'scripts':
          endpoint = '/api/scripts';
          break;
        case 'users':
          endpoint = '/api/accounts';
          break;
        case 'groups':
          endpoint = '/api/groups';
          break;
        default:
          return;
      }
      
      const response = await apiClient.get(endpoint);
      if (response.ok) {
        const data = await response.json();
        // Handle different response structures
        let items = [];
        if (context === 'computers') {
          items = data.computers || data || [];
        } else if (context === 'scripts') {
          items = data.scripts || data || [];
        } else {
          items = data[context] || data || [];
        }
        setHelperData(items);
      } else {
        console.error('Failed to load helper data:', response.status);
        setHelperData([]);
      }
    } catch (error) {
      console.error('Error loading helper data:', error);
      setHelperData([]);
    } finally {
      setHelperLoading(false);
    }
  };

  // Add debounced search functionality
  const [searchTimeout, setSearchTimeout] = useState(null);
  
  const handleHelperSearch = useCallback((searchValue) => {
    setHelperSearch(searchValue);
    
    // Clear existing timeout
    if (searchTimeout) {
      clearTimeout(searchTimeout);
    }
    
    // Set new timeout for search
    const newTimeout = setTimeout(() => {
      if (helperContext === 'computers') {
        loadHelperData(helperContext, searchValue);
      }
      // For other contexts, we filter locally
    }, 300);
    
    setSearchTimeout(newTimeout);
  }, [helperContext, searchTimeout]);

  const handleCursorChange = (e) => {
    const newPosition = e.target.selectionStart;
    setCursorPosition(newPosition);
    
    const context = detectContext(editingXml, newPosition);
    if (context !== helperContext) {
      setHelperContext(context);
      setShowHelperPane(!!context);
      if (context) {
        loadHelperData(context);
      }
    }
  };

  const insertHelperValue = (value, type) => {
    const textarea = document.querySelector('.policy-xml-editor');
    if (!textarea) return;

    const before = editingXml.substring(0, cursorPosition);
    const after = editingXml.substring(cursorPosition);
    
    let insertText = '';
    switch (type) {
      case 'computer':
        insertText = `<computer>\n        <id>${value.id}</id>\n    </computer>`;
        break;
      case 'script':
        insertText = `<script>\n        <id>${value.id}</id>\n        <priority>before</priority>\n    </script>`;
        break;
      case 'user':
        insertText = `<user>\n        <id>${value.id}</id>\n    </user>`;
        break;
      case 'group':
        insertText = `<group>\n        <id>${value.id}</id>\n    </group>`;
        break;
      default:
        insertText = value.toString();
    }
    
    const newContent = before + insertText + after;
    setEditingXml(newContent);
    
    // Update cursor position
    const newPosition = cursorPosition + insertText.length;
    setTimeout(() => {
      textarea.focus();
      textarea.setSelectionRange(newPosition, newPosition);
      setCursorPosition(newPosition);
    }, 0);
  };

  // Enhanced insertHelperValue with smart placement and undo support
  const insertHelperValueEnhanced = (value, type) => {
    const textarea = document.querySelector('.policy-xml-editor');
    if (!textarea) return;
    
    // Determine the container tag based on type
    let containerTag = '';
    switch (type) {
      case 'computer': containerTag = 'computers'; break;
      case 'script': containerTag = 'scripts'; break;
      case 'user': containerTag = 'users'; break;
      case 'group': containerTag = 'groups'; break;
      default: return;
    }
    
    // Find the container in the XML
    const containerStart = `<${containerTag}>`;
    const containerEnd = `</${containerTag}>`;
    const containerStartIndex = editingXml.indexOf(containerStart);
    const containerEndIndex = editingXml.indexOf(containerEnd);
    
    if (containerStartIndex === -1 || containerEndIndex === -1) {
      alert(`Could not find ${containerTag} container in the XML. Please ensure the XML has a proper ${containerTag} section.`);
      return;
    }
    
    // Analyze the container content to determine indentation
    const containerContent = editingXml.substring(
      containerStartIndex + containerStart.length,
      containerEndIndex
    );
    
    // Find existing items in the container to determine proper indentation
    const lines = editingXml.substring(0, containerEndIndex).split('\n');
    const containerLine = lines.find(line => line.includes(containerStart));
    const containerIndent = containerLine ? containerLine.match(/^(\s*)/)[1] : '    ';
    const itemIndent = containerIndent + '    '; // 4 spaces more than container
    const childIndent = itemIndent + '    '; // 4 more spaces for child elements
    
    // Create the new XML element
    let newElement = '';
    switch (type) {
      case 'computer':
        newElement = `${itemIndent}<computer>
${childIndent}<id>${value.id}</id>
${itemIndent}</computer>`;
        break;
      case 'script':
        newElement = `${itemIndent}<script>
${childIndent}<id>${value.id}</id>
${childIndent}<priority>before</priority>
${itemIndent}</script>`;
        break;
      case 'user':
        newElement = `${itemIndent}<user>
${childIndent}<id>${value.id}</id>
${itemIndent}</user>`;
        break;
      case 'group':
        newElement = `${itemIndent}<group>
${childIndent}<id>${value.id}</id>
${itemIndent}</group>`;
        break;
    }
    
    // Check if container is empty or has existing items
    const isContainerEmpty = containerContent.trim().length === 0;
    
    let insertPosition;
    let newContent;
    
    if (isContainerEmpty) {
      // Insert as the first item in empty container
      insertPosition = containerStartIndex + containerStart.length;
      newContent = editingXml.substring(0, insertPosition) + 
                  '\n' + newElement + '\n' + containerIndent + 
                  editingXml.substring(insertPosition);
    } else {
      // Find the first existing item to insert before it (at the top of the list)
      const firstNewlineAfterStart = editingXml.indexOf('\n', containerStartIndex + containerStart.length);
      if (firstNewlineAfterStart !== -1) {
        // Look for the first non-whitespace content after the opening tag
        const contentAfterTag = editingXml.substring(firstNewlineAfterStart + 1, containerEndIndex);
        const firstItemMatch = contentAfterTag.match(/^(\s*)<[^>]+>/);
        
        if (firstItemMatch) {
          // Insert before the first item
          insertPosition = firstNewlineAfterStart + 1;
          newContent = editingXml.substring(0, insertPosition) + 
                      newElement + '\n' + 
                      editingXml.substring(insertPosition);
        } else {
          // Fallback: insert right after the opening tag
          insertPosition = containerStartIndex + containerStart.length;
          newContent = editingXml.substring(0, insertPosition) + 
                      '\n' + newElement + '\n' + containerIndent + 
                      editingXml.substring(insertPosition);
        }
      } else {
        // Fallback: insert right after the opening tag
        insertPosition = containerStartIndex + containerStart.length;
        newContent = editingXml.substring(0, insertPosition) + 
                    '\n' + newElement + '\n' + containerIndent + 
                    editingXml.substring(insertPosition);
      }
    }
    
    // Use proper React state update for undo support
    setEditingXml(newContent);
    
    // Calculate the range of the inserted content for highlighting
    const insertStart = insertPosition + (isContainerEmpty ? 1 : 0); // Account for newline
    const insertEnd = insertStart + newElement.length;
    
    // Focus and highlight the inserted content after React re-renders
    setTimeout(() => {
      textarea.focus();
      // Set selection to highlight the inserted content
      textarea.setSelectionRange(insertStart, insertEnd);
      
      // Add CSS class for visual highlight
      textarea.classList.add('xml-insert-highlight');
      
      // After highlighting, move cursor to end of insertion and remove highlight
      setTimeout(() => {
        textarea.setSelectionRange(insertEnd, insertEnd);
        setCursorPosition(insertEnd);
        textarea.classList.remove('xml-insert-highlight');
      }, 1500); // Highlight for 1.5 seconds
    }, 10); // Small delay to allow React to update
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
            style={isDarkMode ? vscDarkPlus : prism}
            className="xml-viewer"
            customStyle={{
              maxHeight: '70vh',
              fontSize: '0.875rem',
              lineHeight: '1.4',
              borderRadius: '0.375rem',
              backgroundColor: isDarkMode ? '#1e1e1e' : '#ffffff',
              border: `1px solid ${isDarkMode ? '#4a5568' : '#dee2e6'}`,
              padding: '1rem',
              margin: 0
            }}
            showLineNumbers={true}
            lineNumberStyle={{
              color: isDarkMode ? '#858585' : '#6c757d',
              backgroundColor: isDarkMode ? '#252526' : '#f8f9fa',
              paddingRight: '1rem',
              textAlign: 'right',
              borderRight: `1px solid ${isDarkMode ? '#4a5568' : '#dee2e6'}`,
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
              className="form-control policy-xml-editor"
              value={editingXml}
              onChange={(e) => setEditingXml(e.target.value)}
              onInput={handleCursorChange}
              onClick={handleCursorChange}
              onKeyUp={handleCursorChange}
              rows={20}
              style={{ 
                fontFamily: 'Monaco, Consolas, "Courier New", monospace',
                fontSize: '0.875rem',
                marginRight: showHelperPane ? '370px' : '0'
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
            <button 
              className="btn btn-outline-info"
              onClick={() => setShowHelperPane(!showHelperPane)}
            >
              {showHelperPane ? 'Hide Helper' : 'Show Helper'}
            </button>
          </div>
        </div>
        {showHelperPane && (
          <HelperPane 
            showHelperPane={showHelperPane}
            helperContext={helperContext}
            helperData={helperData}
            helperLoading={helperLoading}
            helperSearch={helperSearch}
            onSearchChange={handleHelperSearch}
            onClose={() => setShowHelperPane(false)}
            onInsertValue={insertHelperValueEnhanced}
          />
        )}
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
