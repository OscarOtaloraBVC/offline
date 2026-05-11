import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAllProfiles } from '../../services/profileService';

const ProfileListPage = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    getAllProfiles()
      .then(response => {
        setProfiles(response.data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch profiles.');
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <p>Loading profiles...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Profiles List</h2>
        <Link to="/profiles/new" className="button-link">New Profile</Link>
      </div>
      {profiles.length === 0 ? (
        <p>No profiles found.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {profiles.map(profile => (
              <tr key={profile.id} onClick={() => navigate(`/profiles/${profile.id}`)} style={{cursor: 'pointer'}}>
                <td>{profile.id}</td>
                <td>{profile.name}</td>
                <td>{profile.type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ProfileListPage;