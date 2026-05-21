import { useEffect, useState } from 'react';
import { fetchTeamStats } from '../api/client';
import fallbackData from '../data/teamStatsFallback.json';

export function useTeamStats() {
  const [teams, setTeams] = useState(fallbackData.teams || []);
  const [source, setSource] = useState('fallback');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTeamStats()
      .then((data) => {
        if (data?.teams?.length) {
          setTeams(data.teams);
          setSource('api');
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return { teams, source, loading, error };
}
