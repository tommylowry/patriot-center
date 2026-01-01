import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

/**
 * Hook to fetch summary data for a specific manager.
 *
 * @param {string} managerName - The name of the manager
 * @param {Object} filters - { year?: string|null }
 * @returns {Object} { summary: Object, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagerSummary(managerName, filters = {}) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  const { year } = filters;

  const fetchData = useCallback(async () => {
    if (!managerName) {
      setSummary(null);
      return;
    }

    setLoading(true);
    startLoading();
    setError(null);
    try {
      const endpoint = year
        ? `/api/managers/${encodeURIComponent(managerName)}/summary/${year}`
        : `/api/managers/${encodeURIComponent(managerName)}/summary`;

      const data = await apiGet(endpoint);
      setSummary(data);
    } catch (e) {
      setError(e.message);
      setSummary(null);
    } finally {
      setLoading(false);
      stopLoading();
    }
  }, [managerName, year, startLoading, stopLoading]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { summary, loading, error, refetch: fetchData };
}
