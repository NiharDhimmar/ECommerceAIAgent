import axios from 'axios';

// Use localhost to match frontend origin host for same-site cookies
const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
});

export default api;


