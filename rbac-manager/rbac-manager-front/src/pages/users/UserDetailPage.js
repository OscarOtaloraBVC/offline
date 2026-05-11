import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Swal from 'sweetalert2';
import { getUserById, deleteUser, updateUser, disableUser } from '../../services/userService';
import { getAllProfiles } from '../../services/profileService';
import ManageUserAssignmentsModal from '../../components/modals/ManageUserAssignmentsModal';
import ManageGetKubeconfigModal from '../../components/modals/ManageGetKubeconfigModal';

const UserDetailPage = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [allProfiles, setAllProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAssignmentsModal, setShowAssignmentsModal] = useState(false);
  const [showKubeconfigModal, setShowKubeconfigModal] = useState(false);

  const fetchUserData = useCallback(() => {
    setLoading(true);
    Promise.all([getUserById(userId), getAllProfiles()])
      .then(([userResponse, profilesResponse]) => {
        setUser(userResponse.data);
        setAllProfiles(profilesResponse.data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch user details.');
        console.error(err);
        setLoading(false);
      });
  }, [userId]);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  const handleDelete = async () => {
    const result = await Swal.fire({
      title: 'Are you sure?',
      text: `You are about to delete user "${user?.username}". You won't be able to revert this!`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#d33',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Yes, delete it!'
    });

    if (result.isConfirmed) {
      try {
        await deleteUser(userId);
        Swal.fire('Deleted!', 'The user has been deleted.', 'success');
        navigate('/users');
      } catch (error) {
        Swal.fire({
          icon: 'error',
          title: 'Deletion Failed',
          text: 'Error deleting user.',
        });
      }
    }
  };

  const handleDisableStatus = async () => {
    if (user.state === 'DISABLED') return;

    const result = await Swal.fire({
      title: 'Disable User?',
      text: `Are you sure you want to disable user "${user?.username}"? This will clean up their current resources.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#f39c12',
      cancelButtonColor: '#3085d6',
      confirmButtonText: 'Yes, disable it!'
    });

    if (result.isConfirmed) {
      Swal.fire({
        title: 'Processing...',
        text: 'Cleaning up resources and disabling user, please wait.',
        allowOutsideClick: false,
        didOpen: () => {
          Swal.showLoading();
        }
      });

      try {
        await disableUser(userId);
        
        await Swal.fire({
          icon: 'success',
          title: 'User Disabled',
          text: `User "${user?.username}" is now disabled.`,
          timer: 2000,
          showConfirmButton: false
        });
        
        fetchUserData(); 
      } catch (error) {
        console.error("Status update error:", error);
        Swal.fire({
          icon: 'error',
          title: 'Update Failed',
          text: 'The user status could not be changed or resources could not be cleaned up.',
        });
      }
    }
  };

  const handleManageAssignmentsSave = async (newAssignments) => {
    try {
      const updatedUserData = {
        cert_days: user.cert_days,
        observations: user.observations,
        username: user.username,
        state: user.state,
        assignments: newAssignments,
      };
      const response = await updateUser(userId, updatedUserData);
      setUser(response.data);
      setShowAssignmentsModal(false);
      Swal.fire({
        icon: 'success',
        title: 'Updated!',
        text: 'User assignments have been updated.',
        timer: 1500,
        showConfirmButton: false
      });
      fetchUserData();
    } catch (error) {
      Swal.fire({
        icon: 'error',
        title: 'Update Failed',
        text: 'Error updating assignments.',
      });
    }
  };

  if (loading) return <p>Loading user details...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;
  if (!user) return <p>User not found.</p>;

  return (
    <div>
      <h2>User Details: {user.username}</h2>

      <div className="detail-section">
        <h3>General Information</h3>
        <p><strong>ID:</strong> {user.id}</p>
        <p><strong>Username:</strong> {user.username}</p>
        <p>
          <strong>Status:</strong> 
          <span style={{
            display: 'inline-block',
            padding: '2px 8px',
            marginLeft: '10px',
            borderRadius: '12px',
            fontSize: '0.85em',
            fontWeight: 'bold',
            backgroundColor: user.state === 'ENABLED' ? '#c8e6c9' : '#ffcdd2',
            color: user.state === 'ENABLED' ? '#2e7d32' : '#c62828'
          }}>
            {user.state}
          </span>
        </p>
        <p><strong>Certificate Days:</strong> {user.cert_days}</p>
        <p><strong>Observations:</strong> {user.observations || 'N/A'}</p>
        <p><strong>Last Updated:</strong> {new Date(user.updated_at).toLocaleString()}</p>
      </div>

      <div className="detail-section">
        <h3>Profile & Namespace Assignments</h3>
        {user.assignments && user.assignments.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Namespace</th>
                <th>Profile</th>
              </tr>
            </thead>
            <tbody>
              {user.assignments.map((assignment, index) => (
                <tr key={`${assignment.profile.id}-${assignment.namespace}-${index}`}>
                  <td>{assignment.namespace}</td>
                  <td>{assignment.profile.name} <span style={{ color: 'gray' }}>({assignment.profile.type})</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p>No assignments defined.</p>
        )}
        <button onClick={() => setShowAssignmentsModal(true)} className="secondary">Manage Assignments</button>
      </div>

      <div className="detail-actions">
        <Link to={`/users/${userId}/edit`} className="button-link">Edit</Link>
        
        <button 
          onClick={handleDisableStatus} 
          disabled={user.state === 'DISABLED'}
          style={{ 
            backgroundColor: user.state === 'DISABLED' ? '#ccc' : '#f39c12', 
            color: 'white',
            cursor: user.state === 'DISABLED' ? 'not-allowed' : 'pointer',
            opacity: user.state === 'DISABLED' ? 0.7 : 1
          }}
        >
          Disable User
        </button>

        <button onClick={() => setShowKubeconfigModal(true)} className="secondary">Get Kubeconfig...</button>
        <button onClick={handleDelete} className="danger">Delete</button>
      </div>
      
      {showAssignmentsModal && (
        <ManageUserAssignmentsModal
          currentUserAssignments={user.assignments || []}
          allProfiles={allProfiles}
          onClose={() => setShowAssignmentsModal(false)}
          onSave={handleManageAssignmentsSave}
        />
      )}
      
      {showKubeconfigModal && (
        <ManageGetKubeconfigModal
          user={user}
          onClose={() => setShowKubeconfigModal(false)}
        />
      )}
    </div>
  );
};

export default UserDetailPage;
