// frontend/src/services/alertService.js
import apiClient from './api';

export const getUserAlerts = (userId) => apiClient.get(`/alerts/user/${userId}`);
export const createAlert = (alertData) => apiClient.post('/alerts/', alertData);
export const deleteAlert = (alertId) => apiClient.delete(`/alerts/${alertId}`);
export const notifyNow = (alertId) => apiClient.post(`/alerts/${alertId}/notify-now`);