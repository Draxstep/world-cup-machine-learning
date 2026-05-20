/**
 * useTeams - hook para cargar la lista de equipos al montar la app.
 * Carga una sola vez y cachea en estado local.
 */
import { useState, useEffect } from 'react';
import { fetchTeams } from '../api/client';

export function useTeams() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTeams()
      .then((data) => setTeams(data.teams))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { teams, loading, error };
}
