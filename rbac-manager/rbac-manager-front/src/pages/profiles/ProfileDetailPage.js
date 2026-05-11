import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getProfileById, deleteProfile, getPermissions, saveProfilePermissions } from '../../services/profileService';
import ManageProfilePermissionsModal from '../../components/modals/ManageProfilePermissionsModal';
import Swal from 'sweetalert2';

const ProfileDetailPage = () => {
  const { profileId } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showPermissionsModal, setShowPermissionsModal] = useState(false);

  const userCanViewThisProfilePage = true;
  const userCanCreateOrUpdateProfilePermissions = true;
  const userCanDeleteThisProfile = true;

  const fetchProfileData = useCallback(async () => {
    if (!userCanViewThisProfilePage) {
      setError('You do not have permission to view profile details.');
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const profileResponse = await getProfileById(profileId);
      const fetchedProfileBase = profileResponse.data;

      const permissionsResponse = await getPermissions(profileId); // Expects { data: [...] }
      //console.log("Permissions response from service:", permissionsResponse); // Good for debugging

      setProfile({
        ...fetchedProfileBase,
        permissions: permissionsResponse.data || [], // Correctly using .data
      });

    } catch (err) {
      setError('Failed to fetch profile details or its associated permissions.');
      console.error('Fetch error:', err.response?.data || err.message || err);
    } finally {
      setLoading(false);
    }
  }, [profileId, userCanViewThisProfilePage]);

  useEffect(() => {
    fetchProfileData();
  }, [fetchProfileData]);

  const handleDelete = async () => {
    if (!userCanDeleteThisProfile) {
      Swal.fire({
        icon: 'error',
        title: 'Permission Denied',
        text: 'You do not have permission to delete this profile.',
      });
      return;
    }

    const result = await Swal.fire({
      title: 'Are you sure?',
      text: `You are about to delete profile "${profile?.name}". You won't be able to revert this!`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Yes, delete it!'
    });

    if (result.isConfirmed) {
      try {
        await deleteProfile(profileId);
        Swal.fire(
          'Deleted!',
          'The profile has been deleted.',
          'success'
        );
        navigate('/profiles');
      } catch (error) {
        console.error('Failed to delete profile:', error.response?.data || error.message);
        Swal.fire({
          icon: 'error',
          title: 'Deletion Failed',
          text: `Error deleting profile: ${error.response?.data?.detail || 'Failed to delete'}`,
        });
      }
    }
  };

  const handleManagePermissionsSave = (updatedProfilePermissions) => {
    if (!userCanCreateOrUpdateProfilePermissions) {
      Swal.fire({
        icon: 'error',
        title: 'Permission Denied',
        text: 'You do not have permission to modify profile permissions.',
      });
      return;
    }

    saveProfilePermissions(updatedProfilePermissions, profileId);

    setProfile(prevProfile => ({
      ...prevProfile,
      permissions: updatedProfilePermissions
    }));

    setShowPermissionsModal(false);
  };

  if (loading) return <p>Loading profile details...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;
  if (!profile) return <p>Profile not found.</p>;

  return (
    <div>
      <h2>Profile Details: {profile.name}</h2>

      <div className="detail-section">
        <h3>General Information</h3>
        <p><strong>ID:</strong> {profile.id}</p>
        <p><strong>Name:</strong> {profile.name}</p>
        <p><strong>Type:</strong> <b style={{ color: "orange" }}>{profile.type}</b></p>
      </div>

      {profile.type === 'Customized' && (
        <div className="detail-section">
          <h3>Permissions Defined for this Profile</h3>
          {profile.permissions && profile.permissions.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Resource</th>
                  <th>API Group</th>
                  <th>Namespaced</th>
                  <th>Get</th>
                  <th>List</th>
                  <th>Watch</th>
                  <th>Create</th>
                  <th>Update</th>
                  <th>Patch</th>
                  <th>Delete</th>
                  <th>DeleteCollection</th>
                </tr>
              </thead>
              <tbody>
                {/*
                  Removed comments from inside here and adjusted structure
                  to prevent whitespace text nodes as children of <tr>
                */}
                {profile.permissions.map((perm, index) => (
                  <tr key={perm.id || `perm-${index}`}>
                    <td>{perm.resource}</td>
                    <td>{perm.resource_api || '-'}</td>
                    <td style={{ color: perm.resource_namespaced ? 'blue' : 'orange', textAlign: 'center' }}>{perm.resource_namespaced ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_get ? 'green' : 'gray' }}>{perm.is_verb_get ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_list ? 'green' : 'gray' }}>{perm.is_verb_list ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_watch ? 'green' : 'gray' }}>{perm.is_verb_watch ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_create ? 'green' : 'gray' }}>{perm.is_verb_create ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_update ? 'green' : 'gray' }}>{perm.is_verb_update ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_patch ? 'green' : 'gray' }}>{perm.is_verb_patch ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_delete ? 'green' : 'gray' }}>{perm.is_verb_delete ? 'Yes' : 'No'}</td>
                    <td style={{ color: perm.is_verb_deletecollection ? 'green' : 'gray' }}>{perm.is_verb_deletecollection ? 'Yes' : 'No'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No permissions assigned to this profile. Manage to add some.</p>
          )}
        </div>
      )}

      <div className="detail-actions">
        <Link to={`/profiles/${profileId}/edit`} className="button-link">Edit Profile Info</Link>
        {userCanDeleteThisProfile && (
          <button onClick={handleDelete} className="danger">Delete Profile</button>
        )}
        {userCanCreateOrUpdateProfilePermissions && profile.type === 'Customized' && (
          <button onClick={() => setShowPermissionsModal(true)} className="secondary">Manage Permissions</button>
        )}
      </div>

      {showPermissionsModal && (
        <ManageProfilePermissionsModal
          currentPermissions={profile.permissions || []}
          onClose={() => setShowPermissionsModal(false)}
          onSave={handleManagePermissionsSave}
        />
      )}
    </div>
  );
};

export default ProfileDetailPage;