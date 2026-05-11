import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';  // ← Solo esto, sin BrowserRouter
import Layout from './components/Layout';
import HomePage from './pages/HomePage';

import UserListPage from './pages/users/UserListPage';
import UserNewPage from './pages/users/UserNewPage';
import UserDetailPage from './pages/users/UserDetailPage';
import UserEditPage from './pages/users/UserEditPage';

import ProfileListPage from './pages/profiles/ProfileListPage';
import ProfileNewPage from './pages/profiles/ProfileNewPage';
import ProfileDetailPage from './pages/profiles/ProfileDetailPage';
import ProfileEditPage from './pages/profiles/ProfileEditPage';

// 👇 NUEVA PÁGINA DE ALERTAS
import CertificateAlertsPage from './pages/alerts/CertificateAlertsPage';

import './App.css'; // For menu specific styles
import './index.css'; // For global styles

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        
        <Route path="users" element={<UserListPage />} />
        <Route path="users/new" element={<UserNewPage />} />
        <Route path="users/:userId" element={<UserDetailPage />} />
        <Route path="users/:userId/edit" element={<UserEditPage />} />
        
        <Route path="profiles" element={<ProfileListPage />} />
        <Route path="profiles/new" element={<ProfileNewPage />} />
        <Route path="profiles/:profileId" element={<ProfileDetailPage />} />
        <Route path="profiles/:profileId/edit" element={<ProfileEditPage />} />

         {/* 👇 RUTA PARA ALERTAS */}
        <Route path="alerts" element={<CertificateAlertsPage />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;