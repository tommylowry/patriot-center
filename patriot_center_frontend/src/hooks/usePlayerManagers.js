import { useEffect, useState } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

export function usePlayerManagers(playerSlug, { year = null, week = null, manager = null } = {}) {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  useEffect(() => {
    if (!playerSlug) return;
    let active = true;
    setLoading(true);
    startLoading();
    setError(null);

    // Use the new endpoint when manager is specified
    if (manager != null) {
      const segments = [playerSlug, manager];
      if (year != null) segments.push(String(year));
      if (week != null) segments.push(String(week));
      const path = `/get_player_manager_aggregation/${segments.join('/')}`;

      apiGet(path)
        .then(data => {
          if (!active) return;
          setManagers(Array.isArray(data) ? data : []);
        })
        .catch(e => active && setError(e.message))
        .finally(() => {
          if (active) setLoading(false);
          stopLoading();
        });
    } else {
      const segments = [playerSlug];
      if (year != null) segments.push(String(year));
      if (week != null) segments.push(String(week));
      const path = `/get_aggregated_managers/${segments.join('/')}`;

      apiGet(path)
        .then(data => {
          if (!active) return;
          setManagers(Array.isArray(data) ? data : []);
        })
        .catch(e => active && setError(e.message))
        .finally(() => {
          if (active) setLoading(false);
          stopLoading();
        });
    }

    return () => { active = false; };
  }, [playerSlug, year, week, manager, startLoading, stopLoading]);

  return { managers, loading, error };
}