/**
 * client.js
 * Instancia axios con base URL y funciones tipadas para cada endpoint.
 * El componente o hook importa una funcion, nunca la URL en crudo.
 */
import axios from 'axios';

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail ?? err.message;
    return Promise.reject(new Error(detail));
  }
);

export const fetchTeams = () =>
  http.get('/predict/teams').then((r) => r.data);

export const fetchRiskMap = (teamName, isKnockout, isHome) =>
  http.post('/predict/risk-map', {
    team_name: teamName,
    is_knockout: isKnockout,
    is_home: isHome,
  }).then((r) => r.data);

export const fetchTeamProfile = (teamName) =>
  http.get(`/predict/profile/${encodeURIComponent(teamName)}`).then((r) => r.data);

export const fetchMetrics = () =>
  http.get('/stats/metrics').then((r) => r.data);

export const fetchClusters = () =>
  http.get('/stats/clusters').then((r) => r.data);

export const fetchQuality = () =>
  http.get('/stats/quality').then((r) => r.data);
