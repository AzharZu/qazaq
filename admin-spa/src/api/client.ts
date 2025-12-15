import AuthService from "../services/AuthService";

// Re-export the shared axios instance from AuthService
export const api = AuthService.api;
export default api;
