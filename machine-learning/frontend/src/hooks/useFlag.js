import { useEffect, useState } from 'react';
import { getFlagUrl } from '../utils/flags';

export function useFlag(teamName, useApi) {
  const [url, setUrl] = useState(null);

  useEffect(() => {
    let mounted = true;
    if (!teamName) return;

    getFlagUrl(teamName, useApi)
      .then((flagUrl) => {
        if (mounted) setUrl(flagUrl);
      })
      .catch(() => {
        if (mounted) setUrl(null);
      });

    return () => {
      mounted = false;
    };
  }, [teamName, useApi]);

  return url;
}
