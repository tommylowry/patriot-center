import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';

/**
 * Hook to fetch detailed yearly data for a specific manager.
 *
 * @param {string} managerName - The name of the manager
 * @param {string} year - The year to fetch data for
 * @returns {Object} { yearlyData: Object, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagerYearlyData(managerName, year) {
  const [yearlyData, setYearlyData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    if (!managerName || !year) {
      setYearlyData(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await apiGet(`/api/managers/${encodeURIComponent(managerName)}/yearly/${year}`);
      setYearlyData(data);
    } catch (e) {
      setError(e.message);
      setYearlyData(null);
    } finally {
      setLoading(false);
    }
  }, [managerName, year]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { yearlyData, loading, error, refetch: fetchData };
}
