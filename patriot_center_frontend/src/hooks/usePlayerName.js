import { useEffect, useState } from 'react';
import { apiGet } from '../config/api';

export function usePlayerName(playerSlug) {
  const [playerName, setPlayerName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!playerSlug) {
      setPlayerName('');
      setLoading(false);
      return;
    }

    let active = true;
    setLoading(true);
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
      .finally(() => active && setLoading(false));

    return () => { active = false; };
  }, [playerSlug]);

  return { playerName, loading, error };
}
