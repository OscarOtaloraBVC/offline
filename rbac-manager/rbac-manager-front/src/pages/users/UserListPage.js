import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAllUsers } from '../../services/userService';

const UserListPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    getAllUsers()
      .then(response => {
        setUsers(response.data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch users. Please try again later.');
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading users...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  const badgeStyle = {
    display: 'inline-block',
    padding: '2px 8px',
    margin: '2px',
    backgroundColor: '#e0e0e0',
    borderRadius: '12px',
    fontSize: '0.85em',
    color: '#333'
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Users List</h2>
        <Link to="/users/new" className="button-link">New User</Link>
      </div>
      {users.length === 0 ? (
        <p>No users found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Status</th>
              <th>Namespaces</th>
              <th>Profiles</th>
              <th>Cert. Days</th>
              <th>Observations</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr 
                key={user.id} 
                onClick={() => navigate(`/users/${user.id}`)} 
                style={{cursor: 'pointer'}}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <td>{user.id}</td>
                <td><strong>{user.username}</strong></td>
                <td>
                  <span style={{
                    ...badgeStyle,
                    backgroundColor: user.state === 'ENABLED' ? '#c8e6c9' : '#ffcdd2',
                    color: user.state === 'ENABLED' ? '#2e7d32' : '#c62828',
                    fontWeight: 'bold'
                  }}>
                    {user.state}
                  </span>
                </td>
                <td>
                  {user.namespaces && user.namespaces.length > 0 ? (
                    user.namespaces.map((ns, idx) => (
                      <span key={idx} style={badgeStyle}>{ns.namespace}</span>
                    ))
                  ) : '-'}
                </td>
                <td>
                  {user.profiles && user.profiles.length > 0 ? (
                    user.profiles.map((prof, idx) => (
                      <span key={idx} style={{...badgeStyle, backgroundColor: '#d1e7ff'}}>{prof.name}</span>
                    ))
                  ) : '-'}
                </td>
                <td>{user.cert_days}</td>
                <td>{user.observations || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default UserListPage;