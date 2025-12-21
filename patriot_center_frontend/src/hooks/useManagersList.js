import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

/**
 * Hook to fetch the list of all managers with their basic info.
 *
 * @returns {Object} { managers: Array, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagersList() {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  const fetchData = useCallback(async () => {
    setLoading(true);
    startLoading();
    setError(null);
    try {
      const data = await apiGet('/get/managers/list');
      setManagers(data.managers || []);
    } catch (e) {
      setError(e.message);
      setManagers([]);
    } finally {
      setLoading(false);
      stopLoading();
    }
  }, [startLoading, stopLoading]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { managers, loading, error, refetch: fetchData };
}
