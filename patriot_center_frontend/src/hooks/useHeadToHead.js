import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';

/**
 * Hook to fetch detailed head-to-head data between two managers.
 *
 * @param {string} manager1 - The name of the first manager
 * @param {string} manager2 - The name of the second manager (opponent)
 * @param {Object} filters - { year?: string|null }
 * @returns {Object} { data: Object, loading: boolean, error: string|null, refetch: Function }
 */
export function useHeadToHead(manager1, manager2, filters = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { year } = filters;

  const fetchData = useCallback(async () => {
    if (!manager1 || !manager2) {
      setData(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const endpoint = year
        ? `/api/managers/${encodeURIComponent(manager1)}/head-to-head/${encodeURIComponent(manager2)}/${year}`
        : `/api/managers/${encodeURIComponent(manager1)}/head-to-head/${encodeURIComponent(manager2)}`;

      const result = await apiGet(endpoint);
      setData(result);
    } catch (e) {
      setError(e.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [manager1, manager2, year]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
