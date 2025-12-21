import { useEffect, useState } from 'react';
import { fetchValidOptions } from '../services/options';
import { useLoading } from '../contexts/LoadingContext';

export function useValidOptions(year = null, week = null, manager = null, player = null, position = null) {
  const [options, setOptions] = useState({
    years: [],
    weeks: [],
    managers: [],
    positions: [],
    players: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  useEffect(() => {
    let active = true;
    setLoading(true);
    startLoading();
    setError(null);

    fetchValidOptions(year, week, manager, player, position)
      .then(json => {
        if (!active) return;

        const validOptions = {
          years: Array.isArray(json?.years) ? json.years.map(y => String(y)) : [],
          weeks: Array.isArray(json?.weeks) ? json.weeks.map(w => Number(w)).filter(Number.isFinite).sort((a, b) => a - b) : [],
          managers: Array.isArray(json?.managers) ? json.managers : [],
          positions: Array.isArray(json?.positions) ? json.positions : [],
          players: Array.isArray(json?.players) ? json.players : []
        };

        setOptions(validOptions);

        if (process.env.NODE_ENV === 'development') {
          console.debug('useValidOptions:', { year, week, manager, player, position, validOptions });
        }
      })
      .catch(e => active && setError(e.message))
      .finally(() => {
        if (active) setLoading(false);
        stopLoading();
      });

    return () => { active = false; };
  }, [year, week, manager, player, position, startLoading, stopLoading]);

  return { options, loading, error };
}
