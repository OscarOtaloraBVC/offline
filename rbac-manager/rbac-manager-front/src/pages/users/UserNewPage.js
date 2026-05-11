import React from 'react';
import { useNavigate } from 'react-router-dom';
import UserForm from '../../components/forms/UserForm';
import { createUser } from '../../services/userService';
import Swal from 'sweetalert2';

const UserNewPage = () => {
  const navigate = useNavigate();

  const handleSubmit = async (data) => {
    try {
      // Assignments are now handled on the UserDetailPage after creation.
      // The 'assignments' field can be omitted on creation.
      const response = await createUser(data);
      await Swal.fire({
        icon: 'success',
        title: 'Created!',
        text: 'User created successfully! You will now be redirected to manage their assignments.',
      });
      // Navigate to the new user's detail page to manage assignments
      navigate(`/users/${response.data.id}`);
    } catch (error) {
      console.error('Failed to create user:', error.response?.data || error.message);
      Swal.fire({
        icon: 'error',
        title: 'Creation Failed',
        text: `Error creating user: ${error.response?.data?.detail || 'Failed to create'}`,
      });
    }
  };

  return (
    <div>
      <h2>Create New User</h2>
      <UserForm onSubmit={handleSubmit} />
    </div>
  );
};

export default UserNewPage;