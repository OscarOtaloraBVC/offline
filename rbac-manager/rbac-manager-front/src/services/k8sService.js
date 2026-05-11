// src/services/k8sService.js
import apiClient from './api';

export const getAvailableNamespaces = async () => {
  try {
    const response = await apiClient.get('/k8s_service/ns');
    // The API returns an array of strings: ["backend-rda", "default", ...]
    // The modal expects [{ "namespace": "xxx" }, ...]
    if (Array.isArray(response.data)) {
      return response.data.map(nsName => ({ namespace: nsName }));
    }
    console.error("API did not return an array for namespaces:", response.data);
    return []; // Return empty array on unexpected format
  } catch (error) {
    console.error("Error fetching available namespaces:", error);
    throw error; // Re-throw to be caught by the component
  }
};


export const getAvailableApiResourcess = async () => {
  try {
    const response = await apiClient.get('/k8s_service/api-resources');
    // The API returns an array of strings: ["backend-rda", "default", ...]
    // The modal expects [{ "namespace": "xxx" }, ...]
    if (Array.isArray(response.data)) {
      return response.data.map(nsName => ({ namespace: nsName }));
    }
    console.error("API did not return an array for namespaces:", response.data);
    return []; // Return empty array on unexpected format
  } catch (error) {
    console.error("Error fetching available namespaces:", error);
    throw error; // Re-throw to be caught by the component
  }
};

export const getLastKubeconfig = async (user_id) => {
  try {
    const response = await apiClient.get('/k8s_service/'+user_id+'/last-kubeconfig');
      return response.data;
   
  } catch (error) {
    console.error("Error fetching available namespaces:", error);
    alert(error);
    throw error; // Re-throw to be caught by the component
  }
};

export const reBuildtKubeconfig = async (user_id) => {
  try {
    const response = await apiClient.get('/k8s_service/'+user_id+'/generate-kubeconfig');
      return response.data;
   
  } catch (error) {
    console.error("Error fetching available namespaces:", error);
    alert(error);
    throw error; // Re-throw to be caught by the component
  }
};