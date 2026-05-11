import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import UserForm from '../../components/forms/UserForm';
import { getUserById, updateUser } from '../../services/userService';
import Swal from 'sweetalert2';

const UserEditPage = () => {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    getUserById(userId)
      .then(response => {
        // The form now only deals with basic user fields.
        // Assignments are managed on the detail page.
        setUser(response.data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch user data for editing.');
        console.error(err);
        setLoading(false);
      });
  }, [userId]);

  const handleSubmit = async (data) => {
    try {
      // The 'assignments' field is not part of this form's data.
      // The backend will not update assignments if the field is missing.
      await updateUser(userId, data);
      Swal.fire({
        icon: 'success',
        title: 'Updated!',
        text: 'User updated successfully!',
        timer: 1500,
        showConfirmButton: false
      });
      navigate(`/users/${userId}`);
    } catch (error) {
      console.error('Failed to update user:', error.response?.data || error.message);
      Swal.fire({
        icon: 'error',
        title: 'Update Failed',
        text: `Error updating user: ${error.response?.data?.detail || 'Failed to update'}`,
      });
    }
  };

  if (loading) return <p>Loading user data...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;
  if (!user) return <p>User not found.</p>;

  return (
    <div>
      <h2>Edit User: {user.username}</h2>
      <UserForm onSubmit={handleSubmit} defaultValues={user} isEdit={true} />
    </div>
  );
};

export default UserEditPage;