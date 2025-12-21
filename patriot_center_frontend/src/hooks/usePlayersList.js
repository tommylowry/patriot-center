import { useEffect, useState } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

export function usePlayersList() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  useEffect(() => {
    let active = true;
    startLoading();

    apiGet('/players/list')
      .then(data => {
        if (!active) return;
        // Data comes as list of records with 'name' field (player ID) and other fields
        setPlayers(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(e => {
        if (!active) return;
        setError(e.message);
        setLoading(false);
      })
      .finally(() => {
        stopLoading();
      });

    return () => { active = false; };
  }, [startLoading, stopLoading]);

  return { players, loading, error };
}
