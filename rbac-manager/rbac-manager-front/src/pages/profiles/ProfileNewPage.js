import React from 'react';
import { useNavigate } from 'react-router-dom';
import ProfileForm from '../../components/forms/ProfileForm';
import { createProfile } from '../../services/profileService';
import Swal from 'sweetalert2';

const ProfileNewPage = () => {
  const navigate = useNavigate();

  const handleSubmit = async (data) => {
    try {
      await createProfile(data);
      Swal.fire({
        icon: 'success',
        title: 'Created!',
        text: 'Profile created successfully!',
      });
      navigate('/profiles');
    } catch (error) {
      console.error('Failed to create profile:', error.response?.data || error.message);
      Swal.fire({
        icon: 'error',
        title: 'Creation Failed',
        text: `Error creating profile: ${error.response?.data?.detail || 'Failed to create'}`,
      });
    }
  };

  return (
    <div>
      <h2>Create New Profile</h2>
      <ProfileForm onSubmit={handleSubmit} />
    </div>
  );
};

export default ProfileNewPage;