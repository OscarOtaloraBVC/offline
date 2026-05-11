import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ProfileForm from '../../components/forms/ProfileForm';
import { getProfileById, updateProfile } from '../../services/profileService';
import Swal from 'sweetalert2';

const ProfileEditPage = () => {
  const { profileId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    getProfileById(profileId)
      .then(response => {
        setProfile(response.data);
        setLoading(false);
      })
      .catch(err => {
        setError('Failed to fetch profile data for editing.');
        console.error(err);
        setLoading(false);
      });
  }, [profileId]);

  const handleSubmit = async (data) => {
    try {
      await updateProfile(profileId, data);
      Swal.fire({
        icon: 'success',
        title: 'Updated!',
        text: 'Profile updated successfully!',
        timer: 1500,
        showConfirmButton: false
      });
      navigate(`/profiles/${profileId}`);
    } catch (error) {
      console.error('Failed to update profile:', error.response?.data || error.message);
      Swal.fire({
        icon: 'error',
        title: 'Update Failed',
        text: `Error updating profile: ${error.response?.data?.detail || 'Failed to update'}`,
      });
    }
  };

  if (loading) return <p>Loading profile data...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;
  if (!profile) return <p>Profile not found.</p>;

  return (
    <div>
      <h2>Edit Profile: {profile.name}</h2>
      <ProfileForm onSubmit={handleSubmit} defaultValues={profile} isEdit={true} />
    </div>
  );
};

export default ProfileEditPage;