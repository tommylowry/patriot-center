import { useEffect, useState } from 'react';
import { fetchValidOptions } from '../services/options';

export function useValidOptions(year = null, week = null, manager = null, player = null) {
  const [options, setOptions] = useState({
    years: [],
    weeks: [],
    managers: [],
    positions: [],
    players: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    fetchValidOptions(year, week, manager, player)
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
          console.debug('useValidOptions:', { year, week, manager, player, validOptions });
        }
      })
      .catch(e => active && setError(e.message))
      .finally(() => active && setLoading(false));

    return () => { active = false; };
  }, [year, week, manager, player]);

  return { options, loading, error };
}
