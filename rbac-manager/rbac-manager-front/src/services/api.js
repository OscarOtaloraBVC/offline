// frontend/src/services/api.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',  // Ruta relativa, usa el proxy de nginx
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;