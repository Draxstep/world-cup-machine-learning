import { useEffect, useMemo, useState } from 'react';
import { getTeamMetadata } from '../utils/flags';

const CONTINENT_ORDER = [
  'Europa',
  'Sudamerica',
  'Norteamerica',
  'Centroamerica',
  'Caribe',
  'Africa',
  'Asia',
  'Oceania',
  'America',
  'Otros',
];

function formatTeamLabel(team) {
  return String(team || '')
    .replace(/(^\w|\s\w)/g, (match) => match.toUpperCase());
}

export function useTeamCatalog(teams = []) {
  const [catalog, setCatalog] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    setLoading(true);

    Promise.all(
      teams.map(async (team) => {
        const metadata = await getTeamMetadata(team, true);
        return {
          team,
          label: formatTeamLabel(team),
          ...metadata,
        };
      })
    )
      .then((items) => {
        if (active) {
          setCatalog(items);
        }
      })
      .catch(() => {
        if (active) {
          setCatalog(teams.map((team) => ({ team, label: formatTeamLabel(team), flagUrl: null, continent: 'Otros' })));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [teams]);

  const grouped = useMemo(() => {
    const buckets = new Map();

    catalog.forEach((item) => {
      const key = item.continent || 'Otros';
      if (!buckets.has(key)) {
        buckets.set(key, []);
      }
      buckets.get(key).push(item);
    });

    return CONTINENT_ORDER
      .filter((continent) => buckets.has(continent))
      .map((continent) => ({
        continent,
        teams: buckets.get(continent).slice().sort((a, b) => a.label.localeCompare(b.label, 'es')),
      }));
  }, [catalog]);

  return { catalog, grouped, loading };
}
