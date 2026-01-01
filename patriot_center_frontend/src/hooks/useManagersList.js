import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '../config/api';
import { useLoading } from '../contexts/LoadingContext';

/**
 * Hook to fetch the list of all managers with their basic info.
 *
 * @param {boolean} activeOnly - If true, rankings are relative to active managers only
 * @returns {Object} { managers: Array, loading: boolean, error: string|null, refetch: Function }
 */
export function useManagersList(activeOnly = false) {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  useEffect(() => {
    let isMounted = true;

    const fetchData = async () => {
      setLoading(true);
      startLoading();
      setError(null);
      try {
        const endpoint = `/get/managers/list/${activeOnly}?v=2`;
        const data = await apiGet(endpoint);
        if (isMounted) {
          setManagers(data.managers || []);
        }
      } catch (e) {
        if (isMounted) {
          setError(e.message);
          setManagers([]);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
        stopLoading();
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [activeOnly]);

  const refetch = useCallback(async () => {
    setLoading(true);
    startLoading();
    setError(null);
    try {
      const endpoint = `/get/managers/list/${activeOnly}?v=2`;
      const data = await apiGet(endpoint);
      setManagers(data.managers || []);
    } catch (e) {
      setError(e.message);
      setManagers([]);
    } finally {
      setLoading(false);
      stopLoading();
    }
  }, [activeOnly]);

  return { managers, loading, error, refetch };
}
