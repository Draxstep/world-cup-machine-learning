import { useEffect, useState } from 'react';
import { fetchTeamStats } from '../api/client';
import fallbackData from '../data/teamStatsFallback.json';

export function useTeamStats() {
  const [teams, setTeams] = useState(fallbackData.teams || []);
  const [source, setSource] = useState('fallback');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setError(null);
    fetchTeamStats()
      .then((data) => {
        if (active && data?.teams?.length) {
          setTeams(data.teams);
          setSource('api');
        }
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return { teams, source, loading, error };
}
