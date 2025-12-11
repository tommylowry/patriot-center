import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { useAggregatedPlayers } from './hooks/useAggregatedPlayers';
import { PlayerRow } from './components/PlayerRow';
import { useValidOptions } from './hooks/useValidOptions';
import { BrowserRouter as Router, Routes, Route, useSearchParams } from 'react-router-dom';
import PlayerPage from './pages/PlayerPage';
import Layout from './components/Layout';
import ScrollToTop from './components/ScrollToTop';

function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams();

  // State for filters
  const [year, setYear] = useState('2025');
  const [week, setWeek] = useState(null);
  const [manager, setManager] = useState(null);
  const [positionFilter, setPositionFilter] = useState('ALL');

  // Track if we're initializing from URL to prevent loops
  const isInitializedRef = useRef(false);

  // Sync state with URL params ONLY on mount
  useEffect(() => {
    if (isInitializedRef.current) return;

    const yearParam = searchParams.get('year');
    if (yearParam === 'ALL') {
      setYear(null);
    } else {
      setYear(yearParam || '2025');
    }
    setWeek(searchParams.get('week') ? parseInt(searchParams.get('week')) : null);
    setManager(searchParams.get('manager') || null);
    setPositionFilter(searchParams.get('position') || 'ALL');

    isInitializedRef.current = true;
  }, []); // Only run once on mount

  // Fetch dynamic filter options based on current selections
  const { options, loading: optionsLoading, error: optionsError } = useValidOptions(year, week, manager, null, positionFilter !== 'ALL' ? positionFilter : null);

  const { players, loading, error } = useAggregatedPlayers(year, week, manager);

  // Update URL when filters change (after initialization)
  useEffect(() => {
    if (!isInitializedRef.current) return;

    const params = new URLSearchParams();

    if (year === null) {
      params.set('year', 'ALL');
    } else if (year) {
      params.set('year', year);
    }
    if (week) params.set('week', String(week));
    if (manager) params.set('manager', manager);
    if (positionFilter && positionFilter !== 'ALL') params.set('position', positionFilter);

    setSearchParams(params, { replace: true });
  }, [year, week, manager, positionFilter, setSearchParams]);

  const [sortKey, setSortKey] = useState('ffWAR');
  const [sortDir, setSortDir] = useState('desc');

  const toggleSort = (key) => {
    setSortKey(prev => key);
    setSortDir(prev => (key === sortKey ? (prev === 'asc' ? 'desc' : 'asc') : 'asc'));
  };

  const filteredPlayers = positionFilter === 'ALL'
    ? players
    : players.filter(p => p.position === positionFilter);

  // Added: normalize games started for consistent sorting/display
  const normalizedPlayers = filteredPlayers.map(p => ({
    ...p,
    num_games_started: Number(p.num_games_started ?? p.games_started ?? p.started ?? 0),
  }));

  const sortedPlayers = [...normalizedPlayers].sort((a, b) => {
    const dir = sortDir === 'asc' ? 1 : -1;
    let av = a[sortKey];
    let bv = b[sortKey];
    // normalize for string comparison
    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();
    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  // Generate dynamic header based on filters
  const getHeaderText = () => {
    const parts = [];
    if (manager) parts.push(manager);
    if (year) parts.push(year);
    if (week) parts.push(`week ${week}`);

    // Add position with pluralization if not ALL
    if (positionFilter !== 'ALL') {
      const playerCount = filteredPlayers.length;
      if (playerCount === 1) {
        parts.push(positionFilter);
      } else if (playerCount > 1) {
        // Pluralize position
        parts.push(positionFilter + 's');
      }
    }

    return parts.length > 0 ? parts.join(' ') : 'All Data';
  };

  return (
    <div className="App" style={{ paddingTop: '1.5rem' }}>
      {/* Title centered */}
      <h1 style={{ margin: '0 0 1.5rem 0', fontWeight: 700, fontSize: '2rem' }}>
        {getHeaderText()}
      </h1>

      {/* Dropdown filters */}
      <div className="filters-container">
        {/* Season Filter */}
        <div className="filter-dropdown">
          <label htmlFor="year-select">Season</label>
          <select
            id="year-select"
            value={year === null ? 'ALL' : year}
            onChange={(e) => {
              const val = e.target.value;
              if (val === 'ALL') {
                setYear(null);
                setWeek(null);
              } else {
                setYear(val);
              }
            }}
            disabled={optionsLoading || optionsError}
          >
            <option value="ALL">All Seasons</option>
            {options.years.map(y => (
              <option key={y} value={String(y)}>{y}</option>
            ))}
          </select>
        </div>

        {/* Week Filter */}
        <div className="filter-dropdown">
          <label htmlFor="week-select">Week</label>
          <select
            id="week-select"
            value={week === null ? 'ALL' : week}
            onChange={(e) => {
              const val = e.target.value;
              setWeek(val === 'ALL' ? null : parseInt(val));
            }}
            disabled={!year || optionsLoading || optionsError}
          >
            <option value="ALL">All Weeks</option>
            {(year ? options.weeks : []).map(w => (
              <option key={w} value={w}>Week {w}</option>
            ))}
          </select>
        </div>

        {/* Manager Filter */}
        <div className="filter-dropdown">
          <label htmlFor="manager-select">Manager</label>
          <select
            id="manager-select"
            value={manager === null ? 'ALL' : manager}
            onChange={(e) => {
              const val = e.target.value;
              setManager(val === 'ALL' ? null : val);
            }}
            disabled={optionsLoading || optionsError}
          >
            <option value="ALL">All Managers</option>
            {options.managers.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {/* Position Filter */}
        <div className="filter-dropdown">
          <label htmlFor="position-select">Position</label>
          <select
            id="position-select"
            value={positionFilter}
            onChange={(e) => setPositionFilter(e.target.value)}
            disabled={optionsLoading || optionsError}
          >
            <option value="ALL">All Positions</option>
            {options.positions.map(pos => (
              <option key={pos} value={pos}>{pos}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Clear Filters Button - only show if filters are not at default */}
      {(year !== '2025' || week !== null || manager !== null || positionFilter !== 'ALL') && (
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
          <button
            onClick={() => {
              setYear('2025');
              setWeek(null);
              setManager(null);
              setPositionFilter('ALL');
            }}
            style={{
              padding: '10px 20px',
              background: 'var(--accent)',
              border: 'none',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 15,
              fontWeight: 600,
              color: 'white',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
            }}
            onMouseOver={(e) => {
              e.target.style.transform = 'translateY(-1px)';
              e.target.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
            }}
            onMouseOut={(e) => {
              e.target.style.transform = 'translateY(0)';
              e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            }}
          >
            Clear All Filters
          </button>
        </div>
      )}

      {players.length > 0 && (
        <div className="table-wrapper">
          {loading && <div className="loading-overlay">Loading...</div>}
          <table style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('key')}>
                  <span className="col-header-full">Player</span>
                  <span className="col-header-abbr">Player</span>
                  {' '}{sortKey === 'key' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" className="col-position" style={{ cursor: 'pointer' }} onClick={() => toggleSort('position')}>
                  Pos {sortKey === 'position' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('total_points')}>
                  <span className="col-header-full">Points</span>
                  <span className="col-header-abbr">Pts</span>
                  {' '}{sortKey === 'total_points' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('num_games_started')}>
                  <span className="col-header-full">Games Started</span>
                  <span className="col-header-abbr">GS</span>
                  {' '}{sortKey === 'num_games_started' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th align="center" style={{ cursor: 'pointer' }} onClick={() => toggleSort('ffWAR')}>
                  ffWAR {sortKey === 'ffWAR' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedPlayers.map((p, i) => (
                <PlayerRow key={i} player={p} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <Router>
      <ScrollToTop />
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/player/:playerSlug" element={<PlayerPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
