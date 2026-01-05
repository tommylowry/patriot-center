import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

/**
 * Hook to fetch transaction history for a specific manager with filtering.
 *
 * @param {string} managerName - The name of the manager
 * @param {Object} filters - { year?: string }
 * @returns {Object} { transactions: Object, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagerTransactions(managerName, filters = {}) {
  const [transactions, setTransactions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  const { year } = filters;

  const fetchData = useCallback(async () => {
    if (!managerName) {
      setTransactions(null);
      return;
    }

    setLoading(true);
    startLoading();
    setError(null);
    try {
      // Build endpoint with optional parameters
      let endpoint = `/api/managers/${encodeURIComponent(managerName)}/transactions`;

      // Add optional path parameters if provided
      if (year) {
        const yearParam = year || 'all';
        endpoint += `/${yearParam}`;
      }

      const data = await apiGet(endpoint);
      setTransactions(data);
    } catch (e) {
      setError(e.message);
      setTransactions(null);
    } finally {
      setLoading(false);
      stopLoading();
    }
  }, [managerName, year, startLoading, stopLoading]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { transactions, loading, error, refetch: fetchData };
}
