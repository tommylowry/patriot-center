import { useEffect, useState } from 'react';
import { fetchOptions } from '../services/options';
import { useLoading } from '../contexts/LoadingContext';

export function useMetaOptions() {
  const [years, setYears] = useState([]);
  const [weeksByYear, setWeeksByYear] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { startLoading, stopLoading } = useLoading();

  useEffect(() => {
    let active = true;
    setLoading(true);
    startLoading();
    setError(null);
    fetchOptions()
      .then(json => {
        if (!active) return;
        const yrs = Array.isArray(json?.years) ? json.years.map(y => String(y)) : [];
        const globalWeeks = Array.isArray(json?.weeks)
          ? Array.from(new Set(json.weeks.map(n => Number(n)).filter(Number.isFinite))).sort((a, b) => a - b)
          : [];
        const wksByYear = Object.fromEntries(yrs.map(y => [y, globalWeeks]));
        setYears(yrs);
        setWeeksByYear(wksByYear);
        if (process.env.NODE_ENV === 'development') {
          console.debug('dynamic_filtering normalized:', { years: yrs, weeksByYear: wksByYear });
        }
      })
      .catch(e => active && setError(e.message))
      .finally(() => {
        if (active) setLoading(false);
        stopLoading();
      });
    return () => { active = false; };
  }, [startLoading, stopLoading]);

  return { years, weeksByYear, loading, error };
}