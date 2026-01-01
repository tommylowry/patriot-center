import { useEffect, useState } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

export function usePlayerName(playerSlug) {
  const [playerName, setPlayerName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  useEffect(() => {
    if (!playerSlug) {
      setPlayerName('');
      setLoading(false);
      return;
    }

    let active = true;
    setLoading(true);
    startLoading();
    setError(null);

    apiGet(`/slug_to_player_name/${playerSlug}`)
      .then(data => {
        if (!active) return;
        setPlayerName(data.player_name || '');
      })
      .catch(e => {
        if (!active) return;
        setError(e.message);
        // Fallback to decoded slug if API fails
        setPlayerName(decodeURIComponent(playerSlug));
      })
      .finally(() => {
        if (active) setLoading(false);
        stopLoading();
      });

    return () => { active = false; };
  }, [playerSlug, startLoading, stopLoading]);

  return { playerName, loading, error };
}
