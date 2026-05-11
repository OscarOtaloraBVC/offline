import apiClient from './api';

export const getAllProfiles = () => apiClient.get('/profiles/');
export const getProfileById = (id) => apiClient.get(`/profiles/${id}`);
export const createProfile = (profileData) => apiClient.post('/profiles/', profileData);
export const updateProfile = (id, profileData) => apiClient.put(`/profiles/${id}`, profileData);
export const deleteProfile = (id) => apiClient.delete(`/profiles/${id}`);
export const getPermissions = (id) => apiClient.get(`/profiles/${id}/permissions`);
export const saveProfilePermissions = (permissionsDataList, profileId) => {
  return apiClient.post('/profiles/save-permissions', permissionsDataList, {
    params: {
      profile_id: profileId
    }
  });
};

export const getAdditionalResources = () => apiClient.get('/profiles/additional-resources');

// Note: Managing permissions for a profile would ideally have dedicated endpoints
// e.g., POST /profiles/{id}/permissions, DELETE /permissions/{perm_id}
// If not, it might be part of the ProfileUpdate model, similar to user profiles.
// For now, the modal will manage it client-side.