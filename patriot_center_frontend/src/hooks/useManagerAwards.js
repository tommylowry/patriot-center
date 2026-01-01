import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

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
  const { startLoading, stopLoading } = useLoading();

  const fetchData = useCallback(async () => {
    if (!managerName) {
      setAwards(null);
      return;
    }

    setLoading(true);
    startLoading();
    setError(null);
    try {
      const data = await apiGet(`/api/managers/${encodeURIComponent(managerName)}/awards`);
      setAwards(data);
    } catch (e) {
      setError(e.message);
      setAwards(null);
    } finally {
      setLoading(false);
      stopLoading();
    }
  }, [managerName, startLoading, stopLoading]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { awards, loading, error, refetch: fetchData };
}
