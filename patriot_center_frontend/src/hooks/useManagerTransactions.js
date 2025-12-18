import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';

/**
 * Hook to fetch transaction history for a specific manager with filtering.
 *
 * @param {string} managerName - The name of the manager
 * @param {Object} filters - { year?: string, type?: string, limit?: number, offset?: number }
 * @returns {Object} { transactions: Object, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagerTransactions(managerName, filters = {}) {
  const [transactions, setTransactions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { year, type, limit = 50, offset = 0 } = filters;

  const fetchData = useCallback(async () => {
    if (!managerName) {
      setTransactions(null);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      // Build endpoint with optional parameters
      let endpoint = `/api/managers/${encodeURIComponent(managerName)}/transactions`;

      // Add optional path parameters if provided
      if (year || type || limit !== 50 || offset !== 0) {
        const yearParam = year || 'all';
        const typeParam = type || 'all';
        endpoint += `/${yearParam}/${typeParam}/${limit}/${offset}`;
      }

      const data = await apiGet(endpoint);
      setTransactions(data);
    } catch (e) {
      setError(e.message);
      setTransactions(null);
    } finally {
      setLoading(false);
    }
  }, [managerName, year, type, limit, offset]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { transactions, loading, error, refetch: fetchData };
}
