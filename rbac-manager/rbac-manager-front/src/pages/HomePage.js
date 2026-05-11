import React from 'react';
import { Link } from 'react-router-dom';

const HomePage = () => {
  return (
    <div>
      <h2>Welcome to the RBAC Manager Portal</h2>
      <p>Use the menu above to navigate to Users or Profiles management.</p>
      <p>
        <Link to="/users" className="button-link">Go to Users</Link>
        <Link to="/profiles" className="button-link">Go to Profiles</Link>
      </p>
    </div>
  );
};

export default HomePage;