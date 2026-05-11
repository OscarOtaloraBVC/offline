import React from 'react';
import { Outlet } from 'react-router-dom';
import TopMenu from './TopMenu';

const Layout = () => {
  return (
    <>
      <TopMenu />
      <main className="container">
        <Outlet /> {/* Nested routes will render here */}
      </main>
      <div align="center" className="footer">
        <hr/>
        <span style={{ color: 'gray' }}>
        v 1.0.12 - &copy; nuam 2026
        </span>
      </div>
    </>
  );
};

export default Layout;