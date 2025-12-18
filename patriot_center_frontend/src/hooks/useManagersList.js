import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';

/**
 * Hook to fetch the list of all managers with their basic info.
 *
 * @returns {Object} { managers: Array, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagersList() {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiGet('/get/managers/list');
      setManagers(data.managers || []);
    } catch (e) {
      setError(e.message);
      setManagers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { managers, loading, error, refetch: fetchData };
}
