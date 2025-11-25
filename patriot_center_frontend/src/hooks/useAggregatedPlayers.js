import { useEffect, useState, useCallback } from 'react';

const BASE = process.env.REACT_APP_API_BASE || '';

export async function getAggregatedPlayers(year, week, manager) {
  const seg = [];
  if (year != null) seg.push(year);
  if (week != null) seg.push(week);
  if (manager != null) seg.push(manager);
  const url = `${BASE}/get_aggregated_players${seg.length ? '/' + seg.join('/') : ''}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('HTTP ' + res.status);
  const json = await res.json();
  return Array.isArray(json) ? json : [];
}

export function useAggregatedPlayers(year, week, manager) {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sanitize = (m) => m.trim().replace(/\s+/g, '_');

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);
    getAggregatedPlayers(year, week, manager)
      .then(json => setPlayers(json))
      .catch(e => {
        setError(e.message);
        setPlayers([]);
      })
      .finally(() => setLoading(false));
  }, [year, week, manager]);

  useEffect(() => {
    fetchData(); // runs on mount and whenever year/week/manager change
  }, [fetchData]);

  return { players, loading, error, refetch: fetchData };
}