import React, { useState } from 'react';
import ComputerManager from './ComputerManager';
import PolicyManager from './PolicyManager';
import ScriptManager from './ScriptManager';
import AccountManager from './AccountManager';
import ApiManager from './ApiManager';

const Dashboard = ({ sessionId, onLogout }) => {
  const [currentView, setCurrentView] = useState('dashboard');

  const menuItems = [
    {
      title: 'Computers',
      description: 'Search and manage computer inventory',
      icon: '💻',
      action: () => setCurrentView('computers')
    },
    {
      title: 'Policies',
      description: 'View, manage and delete policies',
      icon: '�',
      action: () => setCurrentView('policies')
    },
    {
      title: 'Scripts',
      description: 'Manage and view script details',
      icon: '📜',
      action: () => setCurrentView('scripts')
    },
    {
      title: 'Accounts',
      description: 'Manage user accounts and groups',
      icon: '👥',
      action: () => setCurrentView('accounts')
    },
    {
      title: 'API Management',
      description: 'View API roles and clients',
      icon: '�',
      action: () => setCurrentView('api')
    },
    {
      title: 'Mobile Devices',
      description: 'Manage mobile device inventory',
      icon: '📱',
      action: () => console.log('Mobile Devices - Coming Soon!')
    },
    {
      title: 'Configuration Profiles',
      description: 'Manage configuration profiles',
      icon: '⚙️',
      action: () => console.log('Configuration Profiles - Coming Soon!')
    },
    {
      title: 'Reports',
      description: 'View system reports and analytics',
      icon: '📊',
      action: () => console.log('Reports - Coming Soon!')
    }
  ];

  // Render specific component based on current view
  if (currentView === 'computers') {
    return <ComputerManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
  }
  
  if (currentView === 'policies') {
    return <PolicyManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
  }
  
  if (currentView === 'scripts') {
    return <ScriptManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
  }
  
  if (currentView === 'accounts') {
    return <AccountManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
  }
  
  if (currentView === 'api') {
    return <ApiManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
  }

  // Main dashboard view
  return (
    <div className="card dashboard-card">
      <div className="card-header">
        <h2 className="mb-0">Eve Dashboard</h2>
      </div>
      
      <div className="card-body">
        <p className="text-muted mb-4">Connected successfully! Choose an option below to get started.</p>
        
        <div className="row g-3">
          {menuItems.map((item, index) => (
            <div key={index} className="col-md-6 col-lg-4">
              <div 
                className="card menu-item-card h-100" 
                onClick={item.action}
                style={{ cursor: 'pointer' }}
              >
                <div className="card-body text-center">
                  <div className="display-4 mb-3">{item.icon}</div>
                  <h5 className="card-title">{item.title}</h5>
                  <p className="card-text text-muted">{item.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
