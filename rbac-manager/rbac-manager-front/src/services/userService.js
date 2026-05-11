import apiClient from './api';

export const getAllUsers = () => apiClient.get('/users/');
export const getUserById = (id) => apiClient.get(`/users/${id}`);
export const createUser = (userData) => apiClient.post('/users/', userData);
export const updateUser = (id, userData) => apiClient.put(`/users/${id}`, userData);
export const disableUser = (id) => apiClient.put(`/users/disable/${id}`, {});
export const deleteUser = (id) => apiClient.delete(`/users/${id}`);

// Note: Managing profiles for a user is done by updating the user object itself
// with a list of assignments. The FastAPI backend handles the users_has_profiles_namespaces table.