import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useManagersList } from '../hooks/useManagersList';

/**
 * ManagerRow component - displays a single manager in the table
 */
function ManagerRow({ manager }) {
  const avatarUrl = manager.avatar_urls?.thumbnail || manager.avatar_urls?.full_size;

  return (
    <tr>
      <td>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {avatarUrl && (
            <img
              src={avatarUrl}
              alt={manager.name}
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                objectFit: 'cover',
                border: '2px solid var(--border)'
              }}
            />
          )}
          <Link
            to={`/manager/${encodeURIComponent(manager.name)}`}
            style={{
              color: 'var(--accent)',
              textDecoration: 'none',
              fontWeight: 500
            }}
          >
            {manager.name}
          </Link>
        </div>
      </td>
      <td align="center">{manager.overall_record || '0-0-0'}</td>
      <td align="center">{manager.total_trades || 0}</td>
      <td align="center">{manager.years_active ? manager.years_active.join(', ') : '—'}</td>
    </tr>
  );
}

/**
 * ManagersPage - List view of all managers
 */
export default function ManagersPage() {
  const { managers, loading, error } = useManagersList();

  const [sortKey, setSortKey] = useState('name');
  const [sortDir, setSortDir] = useState('asc');

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sortedManagers = [...managers].sort((a, b) => {
    const dir = sortDir === 'asc' ? 1 : -1;
    let av = a[sortKey];
    let bv = b[sortKey];

    // Handle special cases for sorting
    if (sortKey === 'overall_record') {
      // Extract wins from "W-L-T" format
      const getWins = (record) => parseInt((record || '0-0-0').split('-')[0]);
      av = getWins(a.overall_record);
      bv = getWins(b.overall_record);
    } else if (sortKey === 'years_active') {
      // Sort by number of years
      av = a.years_active ? a.years_active.length : 0;
      bv = b.years_active ? b.years_active.length : 0;
    }

    if (typeof av === 'string') av = av.toLowerCase();
    if (typeof bv === 'string') bv = bv.toLowerCase();

    if (av < bv) return -1 * dir;
    if (av > bv) return 1 * dir;
    return 0;
  });

  return (
    <div className="App" style={{ paddingTop: '1.5rem' }}>
      <h1 style={{ margin: '0 0 1.5rem 0', fontWeight: 700, fontSize: '2rem' }}>
        Managers
      </h1>

      {loading && <p>Loading managers...</p>}
      {error && <p style={{ color: 'var(--danger)' }}>Error: {error}</p>}

      {!loading && !error && managers.length === 0 && (
        <p style={{ color: 'var(--muted)' }}>No managers found.</p>
      )}

      {!loading && managers.length > 0 && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th
                  style={{ cursor: 'pointer' }}
                  onClick={() => toggleSort('name')}
                >
                  <span className="col-header-full">Manager</span>
                  <span className="col-header-abbr">Mgr</span>
                  {' '}{sortKey === 'name' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th
                  align="center"
                  style={{ cursor: 'pointer' }}
                  onClick={() => toggleSort('overall_record')}
                >
                  <span className="col-header-full">Record</span>
                  <span className="col-header-abbr">Rec</span>
                  {' '}{sortKey === 'overall_record' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th
                  align="center"
                  style={{ cursor: 'pointer' }}
                  onClick={() => toggleSort('total_trades')}
                >
                  <span className="col-header-full">Trades</span>
                  <span className="col-header-abbr">Tr</span>
                  {' '}{sortKey === 'total_trades' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
                <th
                  align="center"
                  style={{ cursor: 'pointer' }}
                  onClick={() => toggleSort('years_active')}
                >
                  <span className="col-header-full">Years Active</span>
                  <span className="col-header-abbr">Years</span>
                  {' '}{sortKey === 'years_active' && (sortDir === 'asc' ? '▲' : '▼')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedManagers.map((manager, i) => (
                <ManagerRow key={i} manager={manager} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
