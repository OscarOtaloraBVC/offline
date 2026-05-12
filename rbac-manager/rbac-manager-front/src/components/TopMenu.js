import React from 'react';
import { Link } from 'react-router-dom';
import appLogo from '../assets/logo.png'; // Make sure you have this image
import CertificateSummary from './CertificateSummary';
import '../App.css'; // For specific menu styling

const TopMenu = () => {
  return (
    <header className="app-header">
      <div className="logo-container">
        <img src={appLogo} alt="App Logo" className="app-logo" />
        <h1 style={{ color: "white" }}>RBAC Manager</h1>
      </div>
      {/* Menú centrado - usando flex con espacio entre */}
      <nav className="main-nav" style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
        <ul style={{ display: 'flex', margin: 0, padding: 0, listStyle: 'none' }}>
          <li>
            <Link to="/">Home</Link> {/* Direct link to the homepage */}
          </li>
          <li>
            <span>Users</span>
            <div className="dropdown-content">
              <Link to="/users">List Users</Link>
              <Link to="/users/new">New User</Link>
            </div>
          </li>
          <li>
            <span>Profiles</span>
            <div className="dropdown-content">
              <Link to="/profiles">List Profiles</Link>
              <Link to="/profiles/new">New Profile</Link>
            </div>
          </li>
                    {/* 👇 ITEM EN EL MENÚ */}
          <li>
            <Link to="/alerts" className="alerts-link" style={{ color: '#ff9800' }}>
              ⚠️ Certificate Alerts
            </Link>
          </li>
        </ul>
      </nav>

      
      {/* Resumen de certificados - fijo a la derecha */}
      <div style={{ marginLeft: 'auto', minWidth: 'fit-content' }}>
        <CertificateSummary />
      </div>

    </header>
  );
};

export default TopMenu;