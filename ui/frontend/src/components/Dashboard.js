import React, { useState } from 'react';
import AccountManager from './AccountManager';
import ApiManager from './ApiManager';
import ComputerManager from './ComputerManager';
import ExtensionAttributeManager from './ExtensionAttributeManager';
import PolicyManager from './PolicyManager';
import ScriptManager from './ScriptManager';

const Dashboard = ({ sessionId, onLogout }) => {
  const [currentView, setCurrentView] = useState('dashboard');

  const menuItems = [
    {
      id: 'accounts',
      emoji: '👥',
      title: 'Account Management',
      description: 'Manage Jamf user accounts and groups'
    },
    {
      id: 'api',
      emoji: '🔌',
      title: 'API Management',
      description: 'Manage API clients and roles'
    },
    {
      id: 'computers',
      emoji: '💻',
      title: 'Computer Management',
      description: 'Search and manage computer records'
    },
    {
      id: 'extension-attributes',
      emoji: '🔧',
      title: 'Extension Attributes',
      description: 'Create and manage extension attributes'
    },
    {
      id: 'policies',
      emoji: '📋',
      title: 'Policy Management',
      description: 'Create and manage Jamf policies'
    },
    {
      id: 'scripts',
      emoji: '📜',
      title: 'Script Management',
      description: 'Upload and manage scripts'
    }
  ];

  const renderCurrentView = () => {
    switch (currentView) {
      case 'accounts':
        return <AccountManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
      case 'api':
        return <ApiManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
      case 'computers':
        return <ComputerManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
      case 'extension-attributes':
        return <ExtensionAttributeManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
      case 'policies':
        return <PolicyManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
      case 'scripts':
        return <ScriptManager sessionId={sessionId} onBack={() => setCurrentView('dashboard')} />;
      default:
        return (
          <div className="dashboard-card card">
            <div className="card-header">
              <h2 className="mb-0">Eve - Jamf Management Dashboard</h2>
            </div>
            <div className="card-body">
              <div className="row g-4">
                {menuItems.map((item) => (
                  <div key={item.id} className="col-12 col-sm-6 col-lg-4">
                    <div 
                      className="card h-100 menu-item-card"
                      onClick={() => setCurrentView(item.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <div className="card-body text-center">
                        <div className="mb-3" style={{ fontSize: '2.5rem' }}>
                          {item.emoji}
                        </div>
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
    }
  };

  return (
    <div className="container-fluid">
      <div className="row justify-content-center">
        <div className="col-12">
          {renderCurrentView()}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
