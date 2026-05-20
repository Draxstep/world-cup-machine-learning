/**
 * useRiskMap - hook para obtener el mapa de riesgo on-demand.
 * No hace fetch al montar; expone fetchData(team, knockout, home).
 */
import { useState } from 'react';
import { fetchRiskMap } from '../api/client';

export function useRiskMap() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async (teamName, isKnockout, isHome) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const result = await fetchRiskMap(teamName, isKnockout, isHome);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, fetchData };
}
