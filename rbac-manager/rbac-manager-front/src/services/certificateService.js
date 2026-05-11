// frontend/src/services/certificateService.js 
import apiClient from './api';

// Para el dashboard - SOLO LECTURA
export const getExpiringCertificates = () => apiClient.get('/certificates/expiring');

// Para depuración
export const getAllCertificates = () => apiClient.get('/certificates/all');