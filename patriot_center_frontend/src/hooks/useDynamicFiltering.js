import { useEffect, useState } from 'react';
import { fetchValidOptions } from '../services/options';
import { useLoading } from '../contexts/LoadingContext';

/**
 * Hook to fetch valid filtering options based on selected criteria.
 *
 * @param {string|null} year - The year of the data to filter.
 * @param {string|null} week - The week of the data to filter.
 * @param {string|null} manager - The manager of the data to filter.
 * @param {string|null} player - The player of the data to filter.
 * @param {string|null} position - The position of the data to filter.
 * @returns {Object} { options: Object, loading: boolean, error: string|null }
 */
export function useDynamicFiltering(
  year = null,
  week = null,
  manager = null,
  player = null,
  position = null
) {
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

    // Fetch valid filtering options from the API
    fetchValidOptions(year, week, manager, player, position)
      .then(json => {
        if (!active) return;

        // Normalize the data from the API
        const validOptions = {
          years: Array.isArray(json?.years) ? json.years.map(y => String(y)) : [],
          weeks: Array.isArray(json?.weeks)
            ? json.weeks.map(w => Number(w)).filter(Number.isFinite).sort((a, b) => a - b)
            : [],
          managers: Array.isArray(json?.managers) ? json.managers : [],
          positions: Array.isArray(json?.positions) ? json.positions : [],
          players: Array.isArray(json?.players) ? json.players : []
        };

        setOptions(validOptions);

        // Log the response for debugging purposes
        if (process.env.NODE_ENV === 'development') {
          console.debug('useDynamicFiltering:', {
            year,
            week,
            manager,
            player,
            position,
            validOptions
          });
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
