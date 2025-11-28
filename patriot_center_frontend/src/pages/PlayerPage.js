import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { displayFromSlug } from '../components/player/PlayerNameFormatter';
import { usePlayerManagers } from '../hooks/usePlayerManagers';
import { useMetaOptions } from '../hooks/useMetaOptions';

export default function PlayerPage() {
    const { playerSlug } = useParams();
    const slug = playerSlug || 'Amon-Ra_St._Brown'; // default capitalized
    const displayName = displayFromSlug(slug);

    const { years, weeksByYear, loading: optionsLoading, error: optionsError } = useMetaOptions();

    const [year, setYear] = useState(null);    // default: ALL years
    const [week, setWeek] = useState(null);      // default: ALL weeks
    const [imageError, setImageError] = useState(false);

    React.useEffect(() => {
        setWeek(null);
    }, [year]);

    const { managers, loading, error } = usePlayerManagers(slug, { year, week });

    // Extract player image URL from first manager object
    const playerImageUrl = managers?.[0]?.player_image_endpoint;

    // Reset image error when player changes
    React.useEffect(() => {
        setImageError(false);
    }, [playerImageUrl]);

    // Sorting state + helpers
    const [sortKey, setSortKey] = useState('ffWAR');
    const [sortDir, setSortDir] = useState('desc');
    const toggleSort = (key) => {
        setSortKey(prev => key);
        setSortDir(prev => (key === sortKey ? (prev === 'asc' ? 'desc' : 'asc') : 'asc'));
    };

    // Normalize and sort managers
    const mrows = Array.isArray(managers) ? managers.map(m => ({
        manager: m.manager ?? m.player ?? m.key ?? '',
        total_points: Number(m.total_points ?? m.points ?? 0),
        num_games_started: Number(m.num_games_started ?? m.games_started ?? m.started ?? 0),
        ffWAR: Number(m.ffWAR ?? 0),
    })) : [];

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

    // Fallback: handle year as string/number just in case
    const wk = (year != null)
        ? (weeksByYear[year] ?? [])
        : [];
    const availableWeeks = Array.isArray(wk) ? wk : [];

    if (process.env.NODE_ENV === 'development') {
        console.debug('years:', years, 'weeksByYear:', weeksByYear, 'year:', year, 'availableWeeks:', availableWeeks);
    }

    return (
        <div className="App" style={{ paddingTop: '1rem' }}>

            {/* Player Hero Section */}
            <div style={{
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
                <div>
                    <h1 style={{ margin: 0, marginBottom: '0.25rem' }}>{displayName}</h1>
                    {managers?.[0]?.position && (
                        <p style={{
                            margin: 0,
                            color: 'var(--muted)',
                            fontSize: '1.1rem',
                            fontWeight: 500
                        }}>
                            {managers[0].position}
                        </p>
                    )}
                </div>
            </div>
            <p style={{ marginBottom: '1rem' }}>
                <Link to="/" style={{ color: 'var(--accent)', textDecoration: 'none' }}>
                    ← Back
                </Link>
            </p>
            <div style={{ display: 'inline-flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '0.75rem', justifyContent: 'center' }}>
                <label>
                    Year:{' '}
                    <select
                        value={year ?? ''}
                        disabled={optionsLoading || optionsError}
                        onChange={e => setYear(e.target.value || null)}
                    >
                        <option value="">ALL</option>
                        {years.map(y => <option key={y} value={y}>{y}</option>)}
                    </select>
                </label>
                <label>
                    Week:{' '}
                    <select
                        value={week ?? ''}
                        disabled={optionsLoading || optionsError || year == null}
                        onChange={e => setWeek(e.target.value ? Number(e.target.value) : null)}
                    >
                        <option value="">ALL</option>
                        {(year && Array.isArray(weeksByYear[year]) ? weeksByYear[year] : []).map(w => (
                            <option key={w} value={w}>{w}</option>
                        ))}
                    </select>
                </label>
            </div>

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
                                    Manager {sortKey === 'manager' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('total_points')}>
                                    Total Points {sortKey === 'total_points' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('num_games_started')}>
                                    Games Started {sortKey === 'num_games_started' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                                <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('ffWAR')}>
                                    ffWAR {sortKey === 'ffWAR' && (sortDir === 'asc' ? '▲' : '▼')}
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedManagers.map((m, i) => {
                                const warClass = m.ffWAR > 0 ? 'war-positive' : m.ffWAR < 0 ? 'war-negative' : 'war-neutral';
                                return (
                                    <tr key={i}>
                                        <td>{m.manager || '—'}</td>
                                        <td>{m.total_points}</td>
                                        <td>{m.num_games_started}</td>
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