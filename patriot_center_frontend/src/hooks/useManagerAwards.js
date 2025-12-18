import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';

/**
 * Hook to fetch awards/achievements for a specific manager.
 *
 * @param {string} managerName - The name of the manager
 * @returns {Object} { awards: Object, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagerAwards(managerName) {
  const [awards, setAwards] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    if (!managerName) {
      setAwards(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await apiGet(`/api/managers/${encodeURIComponent(managerName)}/awards`);
      setAwards(data);
    } catch (e) {
      setError(e.message);
      setAwards(null);
    } finally {
      setLoading(false);
    }
  }, [managerName]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { awards, loading, error, refetch: fetchData };
}
