import { useEffect, useState } from 'react';
import { apiGet } from '../config/api';

export function usePlayersList() {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

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
      });

    return () => { active = false; };
  }, []);

  return { players, loading, error };
}
