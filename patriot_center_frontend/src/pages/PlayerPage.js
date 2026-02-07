import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, Link, useSearchParams } from "react-router-dom";
import { usePlayerManagers } from '../hooks/usePlayerManagers';
import { useDynamicFiltering } from '../hooks/useDynamicFiltering';

export default function PlayerPage() {
    const { playerId } = useParams();
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
    const playerIdToUse = playerId || '10859'; // Default to Amon-Ra St. Brown's player_id

    const [year, setYear] = useState(null);    // default: ALL years
    const [week, setWeek] = useState(null);      // default: ALL weeks
    const [manager, setManager] = useState(null);  // default: ALL managers
    const [imageError, setImageError] = useState(false);

    // Track if we're syncing from URL to prevent loops
    const isSyncingFromUrlRef = useRef(false);

    // Sync state from URL params (runs on mount and when URL changes via back/forward)
    useEffect(() => {
        isSyncingFromUrlRef.current = true;

        const yearParam = searchParams.get('year');
        const weekParam = searchParams.get('week');
        const managerParam = searchParams.get('manager');

        setYear(yearParam && yearParam !== 'ALL' ? parseInt(yearParam) : null);
        setWeek(weekParam && weekParam !== 'ALL' ? parseInt(weekParam) : null);
        setManager(managerParam && managerParam !== 'ALL' ? managerParam : null);

        // Reset flag after state updates have been processed
        setTimeout(() => {
            isSyncingFromUrlRef.current = false;
        }, 0);
    }, [searchParams]);

    const { options, loading: optionsLoading, error: optionsError } = useDynamicFiltering(year, week, manager, playerIdToUse);

    // Update URL when filters change from user interaction (not from URL sync)
    useEffect(() => {
        if (isSyncingFromUrlRef.current) return;

        const params = new URLSearchParams();

        if (year !== null) params.set('year', String(year));
        if (week !== null) params.set('week', String(week));
        if (manager !== null) params.set('manager', manager);

        setSearchParams(params);
    }, [year, week, manager, setSearchParams]);

    useEffect(() => {
        setWeek(null);
    }, [year]);

    // Fetch all-time data for medals (unfiltered)
    const { managers: allTimeManagers } = usePlayerManagers(playerIdToUse, {});

    // Fetch filtered data for the table
    const { managers, loading, error } = usePlayerManagers(playerIdToUse, { year, week, manager });

    // Extract player data from first manager object
    const playerImageUrl = managers?.[0]?.player_image_endpoint;
    const displayName = managers?.[0]?.player || allTimeManagers?.[0]?.player || '';

    // Reset image error when player changes
    React.useEffect(() => {
        setImageError(false);
    }, [playerImageUrl]);

    // Count playoff placements and track details for hover (using all-time data)
    const { playoffCounts, playoffDetails } = React.useMemo(() => {
        const counts = { 1: 0, 2: 0, 3: 0 };
        const details = { 1: [], 2: [], 3: [] };

        allTimeManagers.forEach(manager => {
            const managerName = manager.manager || manager.player || manager.key || '';
            // API returns flattened keys like "playoff_placement.PlayerName.2021": 1
            Object.keys(manager).forEach(key => {
                if (key.startsWith('playoff_placement.')) {
                    const placement = manager[key];
                    if (placement === 1 || placement === 2 || placement === 3) {
                        counts[placement]++;
                        // Extract year from key: "playoff_placement.PlayerName.2021" -> "2021"
                        const parts = key.split('.');
                        const year = parts[parts.length - 1];
                        details[placement].push({ manager: managerName, year });
                    }
                }
            });
        });

        // Sort details by year (descending)
        Object.keys(details).forEach(placement => {
            details[placement].sort((a, b) => b.year - a.year);
        });

        return { playoffCounts: counts, playoffDetails: details };
    }, [allTimeManagers]);

    // Sorting state + helpers
    const [sortKey, setSortKey] = useState('ffWAR');
    const [sortDir, setSortDir] = useState('desc');
    const toggleSort = (key) => {
        setSortKey(key);
        setSortDir(prev => (key === sortKey ? (prev === 'asc' ? 'desc' : 'asc') : 'asc'));
    };

    // Normalize and sort managers
    const mrows = Array.isArray(managers) ? managers.map(m => {
        // Extract playoff placements for this specific manager
        const managerPlacements = { 1: [], 2: [], 3: [] };
        Object.keys(m).forEach(key => {
            if (key.startsWith('playoff_placement.')) {
                const placement = m[key];
                if (placement === 1 || placement === 2 || placement === 3) {
                    const parts = key.split('.');
                    const year = parts[parts.length - 1];
                    managerPlacements[placement].push(year);
                }
            }
        });

        return {
            manager: m.manager ?? m.player ?? m.key ?? '',
            total_points: Number(m.total_points ?? m.points ?? 0),
            num_games_started: Number(m.num_games_started ?? m.games_started ?? m.started ?? 0),
            ffWAR_per_game: Number(m.ffWAR_per_game ?? 0),
            ffWAR: Number(m.ffWAR ?? 0),
            placements: managerPlacements
        };
    }) : [];

    const sortedManagers = [...mrows].sort((a, b) => {
        const dir = sortDir === 'asc' ? 1 : -1;
        let av = a[sortKey];
        let bv = b[sortKey];
        if (typeof av === 'string') av = av.toLowerCase();
        if (typeof bv === 'string') bv = bv.toLowerCase();
        if (av < bv) return -1 * dir;
        if (av > bv) return 1 * dir;
        return 0;
    });

    if (process.env.NODE_ENV === 'development') {
        console.debug('options:', options, 'year:', year, 'week:', week);
    }

    return (
        <div className="App" style={{ paddingTop: '1rem' }}>

            {/* Player Hero Section */}
            <div className="player-hero" style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1.5rem',
                marginBottom: '2rem',
                padding: '1.5rem',
                background: 'var(--bg-alt)',
                borderRadius: '12px',
                border: '1px solid var(--border)'
            }}>
                {playerImageUrl && !imageError && (
                    <img
                        src={playerImageUrl}
                        alt={displayName}
                        onError={() => setImageError(true)}
                        style={{
                            width: '120px',
                            height: '120px',
                            objectFit: 'cover',
                            borderRadius: '12px',
                            border: '2px solid var(--border)',
                            backgroundColor: 'var(--bg)',
                            flexShrink: 0
                        }}
                    />
                )}
                <div style={{ flex: 1 }}>
                    <h1 style={{ margin: 0, marginBottom: '0.25rem' }}>{displayName}</h1>
                    {managers?.[0]?.position && (
                        <p style={{
                            margin: 0,
                            color: 'var(--muted)',
                            fontSize: '1.1rem',
                            fontWeight: 500
                        }}>
                            {managers[0].position}{managers[0].team ? ` • ${managers[0].team}` : ''}
                        </p>
                    )}
                </div>
                {/* Playoff Ribbons */}
                {(playoffCounts[1] > 0 || playoffCounts[2] > 0 || playoffCounts[3] > 0) && (
                    <div className="playoff-ribbons" style={{
                        display: 'flex',
                        gap: '1rem',
                        alignItems: 'flex-start',
                        flexShrink: 0
                    }}>
                        {playoffCounts[1] > 0 && (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.1rem'
                            }}>
                                <div style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    gap: '0.05rem',
                                    minHeight: '80px',
                                    justifyContent: 'center'
                                }}>
                                    <div className="emoji" style={{
                                        fontSize: '2.5rem',
                                        lineHeight: 1,
                                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                                    }}>
                                        🥇
                                    </div>
                                    <span style={{
                                        fontSize: '1rem',
                                        fontWeight: 700,
                                        color: 'var(--text)'
                                    }}>
                                        ×{playoffCounts[1]}
                                    </span>
                                </div>
                                <div className="playoff-details" style={{
                                    fontSize: '0.7rem',
                                    color: 'var(--muted)',
                                    textAlign: 'center',
                                    lineHeight: 1.3,
                                    maxWidth: '100px',
                                    borderTop: '1px solid var(--border)',
                                    paddingTop: '0.25rem'
                                }}>
                                    {playoffDetails[1].map((d, i) => (
                                        <div key={i}>{d.year}: {d.manager}</div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {playoffCounts[2] > 0 && (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.1rem'
                            }}>
                                <div style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    gap: '0.05rem',
                                    minHeight: '80px',
                                    justifyContent: 'center'
                                }}>
                                    <div className="emoji" style={{
                                        fontSize: '2.5rem',
                                        lineHeight: 1,
                                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                                    }}>
                                        🥈
                                    </div>
                                    <span style={{
                                        fontSize: '1rem',
                                        fontWeight: 700,
                                        color: 'var(--text)'
                                    }}>
                                        ×{playoffCounts[2]}
                                    </span>
                                </div>
                                <div className="playoff-details" style={{
                                    fontSize: '0.7rem',
                                    color: 'var(--muted)',
                                    textAlign: 'center',
                                    lineHeight: 1.3,
                                    maxWidth: '100px',
                                    borderTop: '1px solid var(--border)',
                                    paddingTop: '0.25rem'
                                }}>
                                    {playoffDetails[2].map((d, i) => (
                                        <div key={i}>{d.year}: {d.manager}</div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {playoffCounts[3] > 0 && (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.1rem'
                            }}>
                                <div style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    gap: '0.05rem',
                                    minHeight: '80px',
                                    justifyContent: 'center'
                                }}>
                                    <div className="emoji" style={{
                                        fontSize: '2.5rem',
                                        lineHeight: 1,
                                        filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))'
                                    }}>
                                        🥉
                                    </div>
                                    <span style={{
                                        fontSize: '1rem',
                                        fontWeight: 700,
                                        color: 'var(--text)'
                                    }}>
                                        ×{playoffCounts[3]}
                                    </span>
                                </div>
                                <div className="playoff-details" style={{
                                    fontSize: '0.7rem',
                                    color: 'var(--muted)',
                                    textAlign: 'center',
                                    lineHeight: 1.3,
                                    maxWidth: '100px',
                                    borderTop: '1px solid var(--border)',
                                    paddingTop: '0.25rem'
                                }}>
                                    {playoffDetails[3].map((d, i) => (
                                        <div key={i}>{d.year}: {d.manager}</div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
            <p style={{ marginBottom: '1rem' }}>
                <button
                    onClick={() => navigate(-1)}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: 'var(--accent)',
                        textDecoration: 'none',
                        cursor: 'pointer',
                        fontSize: 'inherit',
                        fontFamily: 'inherit',
                        padding: 0
                    }}
                >
                    ← Back
                </button>
            </p>

            {/* Dropdown filters */}
            <div className="filters-container">
                {/* Season Filter */}
                <div className="filter-dropdown">
                    <label htmlFor="player-year-select">Season</label>
                    <select
                        id="player-year-select"
                        value={year === null ? 'ALL' : year}
                        onChange={(e) => {
                            const val = e.target.value;
                            if (val === 'ALL') {
                                setYear(null);
                                setWeek(null);
                            } else {
                                setYear(parseInt(val));
                            }
                        }}
                        disabled={optionsLoading || optionsError}
                    >
                        <option value="ALL">All Seasons</option>
                        {options.years.map(y => (
                            <option key={y} value={y}>{y}</option>
                        ))}
                    </select>
                </div>

                {/* Week Filter */}
                <div className="filter-dropdown">
                    <label htmlFor="player-week-select">Week</label>
                    <select
                        id="player-week-select"
                        value={week === null ? 'ALL' : week}
                        onChange={(e) => {
                            const val = e.target.value;
                            setWeek(val === 'ALL' ? null : parseInt(val));
                        }}
                        disabled={optionsLoading || optionsError}
                    >
                        <option value="ALL">All Weeks</option>
                        {(year ? options.weeks : []).map(w => (
                            <option key={w} value={w}>Week {w}</option>
                        ))}
                    </select>
                </div>

                {/* Manager Filter */}
                <div className="filter-dropdown">
                    <label htmlFor="player-manager-select">Manager</label>
                    <select
                        id="player-manager-select"
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
            </div>

            {/* Clear Filters Button - only show if filters are not at default */}
            {(year !== null || week !== null || manager !== null) && (
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.5rem' }}>
                    <button
                        onClick={() => {
                            setYear(null);
                            setWeek(null);
                            setManager(null);
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

            {loading && <p>Loading manager breakdown...</p>}
            {error && !loading && <p style={{ color: 'var(--danger)' }}>{error}</p>}
            {!loading && !error && mrows.length === 0 && (
                <p style={{ color: 'var(--muted)' }}>No manager stats found.</p>
            )}

            {!loading && mrows.length > 0 && (
                <div className="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('manager')}>
                                    <span className="col-header-full">Manager</span>
                                    <span className="col-header-abbr">Mgr</span>
                                    {' '}{sortKey === 'manager' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('total_points')}>
                                    <span className="col-header-full">Total Points</span>
                                    <span className="col-header-abbr">Pts</span>
                                    {' '}{sortKey === 'total_points' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('num_games_started')}>
                                    <span className="col-header-full">Games Started</span>
                                    <span className="col-header-abbr">GS</span>
                                    {' '}{sortKey === 'num_games_started' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('ffWAR_per_game')}>
                                    <span className="col-header-full">ffWAR/G</span>
                                    <span className="col-header-abbr">WAR/G</span>
                                    {' '}{sortKey === 'ffWAR_per_game' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('ffWAR')}>
                                    ffWAR {sortKey === 'ffWAR' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedManagers.map((m, i) => {
                                const warClass = m.ffWAR > 0 ? 'war-positive' : m.ffWAR < 0 ? 'war-negative' : 'war-neutral';
                                const hasPlacements = m.placements[1].length > 0 || m.placements[2].length > 0 || m.placements[3].length > 0;

                                return (
                                    <tr key={i}>
                                        <td>
                                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                                                {m.manager ? (
                                                    <Link
                                                        to={`/manager/${encodeURIComponent(m.manager)}`}
                                                        style={{
                                                            color: 'var(--accent)',
                                                            textDecoration: 'none',
                                                            fontWeight: 500
                                                        }}
                                                    >
                                                        {m.manager}
                                                    </Link>
                                                ) : (
                                                    <span>—</span>
                                                )}
                                                {hasPlacements && (
                                                    <div style={{ display: 'flex', gap: '0.15rem' }}>
                                                        {/* Show one ribbon per year for 1st place */}
                                                        {m.placements[1].map((year, idx) => (
                                                            <span
                                                                key={`1-${idx}`}
                                                                className="ribbon-tooltip"
                                                                data-tooltip={`${year}`}
                                                                style={{ fontSize: '1.2rem', cursor: 'pointer' }}
                                                            >
                                                                🥇
                                                            </span>
                                                        ))}
                                                        {/* Show one ribbon per year for 2nd place */}
                                                        {m.placements[2].map((year, idx) => (
                                                            <span
                                                                key={`2-${idx}`}
                                                                className="ribbon-tooltip"
                                                                data-tooltip={`${year}`}
                                                                style={{ fontSize: '1.2rem', cursor: 'pointer' }}
                                                            >
                                                                🥈
                                                            </span>
                                                        ))}
                                                        {/* Show one ribbon per year for 3rd place */}
                                                        {m.placements[3].map((year, idx) => (
                                                            <span
                                                                key={`3-${idx}`}
                                                                className="ribbon-tooltip"
                                                                data-tooltip={`${year}`}
                                                                style={{ fontSize: '1.2rem', cursor: 'pointer' }}
                                                            >
                                                                🥉
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td>{m.total_points}</td>
                                        <td>{m.num_games_started}</td>
                                        <td>{Number(m.ffWAR_per_game).toFixed(3)}</td>
                                        <td className={warClass}>{m.ffWAR}</td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
