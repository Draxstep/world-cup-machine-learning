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

const jsonCache = new Map();
const profileCache = new Map();

function cacheJson(key, request) {
  if (jsonCache.has(key)) {
    return jsonCache.get(key);
  }

  const promise = request()
    .then((response) => response.data)
    .catch((error) => {
      jsonCache.delete(key);
      throw error;
    });

  jsonCache.set(key, promise);
  return promise;
}

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail ?? err.message;
    return Promise.reject(new Error(detail));
  }
);

export const fetchTeams = () =>
  cacheJson('predict/teams', () => http.get('/predict/teams'));

export const fetchRiskMap = (teamName, isKnockout, isHome) =>
  http.post('/predict/risk-map', {
    team_name: teamName,
    is_knockout: isKnockout,
    is_home: isHome,
  }).then((r) => r.data);

export const fetchTeamProfile = (teamName) =>
  {
    const key = `predict/profile/${String(teamName || '').toLowerCase()}`;
    if (!profileCache.has(key)) {
      profileCache.set(
        key,
        http.get(`/predict/profile/${encodeURIComponent(teamName)}`)
          .then((r) => r.data)
          .catch((error) => {
            profileCache.delete(key);
            throw error;
          })
      );
    }
    return profileCache.get(key);
  };

export const fetchMetrics = () =>
  cacheJson('stats/metrics', () => http.get('/stats/metrics'));

export const fetchClusters = () =>
  cacheJson('stats/clusters', () => http.get('/stats/clusters'));

export const fetchQuality = () =>
  cacheJson('stats/quality', () => http.get('/stats/quality'));

export const fetchReport = (format = 'pdf') =>
  http.get('/stats/report', {
    params: { format },
    responseType: 'blob',
  }).then((r) => ({
    blob: r.data,
    contentType: r.headers['content-type'],
    contentDisposition: r.headers['content-disposition'],
  }));

export const fetchTeamReport = ({ team, format = 'pdf', mode = 'heatmap', is_knockout = 0, is_home = 1 }) =>
  http.get('/stats/report/team', {
    params: { team, format, mode, is_knockout, is_home },
    responseType: 'blob',
  }).then((r) => ({
    blob: r.data,
    contentType: r.headers['content-type'],
    contentDisposition: r.headers['content-disposition'],
  }));

export const fetchTeamStats = () =>
  cacheJson('stats/teams', () => http.get('/stats/teams'));
