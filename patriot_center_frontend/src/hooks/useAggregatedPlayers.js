import { useEffect, useState, useCallback } from 'react';
import { apiGet, sanitizeManager } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

function buildAggregatedPlayersPath(year, manager, week) {
  const seg = [];
  if (year != null) seg.push(year);
  if (manager != null && String(manager).trim()) seg.push(sanitizeManager(manager));
  if (week != null) seg.push(week);
  return '/get_aggregated_players' + (seg.length ? '/' + seg.join('/') : '');
}

export async function getAggregatedPlayers(year, week, manager) {
  const path = buildAggregatedPlayersPath(year, manager, week);
  const json = await apiGet(path);
  return Array.isArray(json) ? json : [];
}

export function useAggregatedPlayers(year, week, manager) {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  const fetchData = useCallback(() => {
    setLoading(true);
    startLoading();
    setError(null);
    getAggregatedPlayers(year, week, manager)
      .then(setPlayers)
      .catch(e => { setError(e.message); setPlayers([]); })
      .finally(() => {
        setLoading(false);
        stopLoading();
      });
  }, [year, week, manager, startLoading, stopLoading]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return { players, loading, error, refetch: fetchData };
}