import React, { useState } from 'react';
import { useManagersList } from '../hooks/useManagersList';
import { ManagerCard } from '../components/ManagerCard';

/**
 * ManagersPage - Card-based grid view of all managers
 */
export default function ManagersPage() {
  const [filterActive, setFilterActive] = useState('all'); // 'all' or 'active'

  // Fetch managers with rankings relative to the selected filter
  const activeOnly = filterActive === 'active';
  const { managers, loading, error } = useManagersList(activeOnly);

  // Filter managers (client-side filtering when showing active only)
  const filteredManagers = managers.filter(manager => {
    if (filterActive === 'active') return manager.is_active;
    return true;
  });

  // Sort managers by weight (descending - higher weight = higher on list)
  const sortedManagers = [...filteredManagers].sort((a, b) => {
    const weightA = a.weight || 0;
    const weightB = b.weight || 0;
    return weightB - weightA; // Descending order
  });

  const filterOptions = [
    { key: 'all', label: 'All Managers' },
    { key: 'active', label: 'Active Only' }
  ];

  return (
    <div className="App" style={{ paddingTop: '1.5rem' }}>
      {/* Page Header */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginBottom: '2rem',
        gap: '0.5rem'
      }}>
        <h1 style={{
          margin: 0,
          fontWeight: 700,
          fontSize: '2.5rem',
          letterSpacing: '1px',
          textTransform: 'uppercase'
        }}>
          Managers
        </h1>
        <div style={{
          fontSize: '0.9rem',
          color: 'var(--muted)'
        }}>
          {managers.length} {managers.length === 1 ? 'manager' : 'managers'} in the league
        </div>
      </div>

      {loading && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
          Loading managers...
        </div>
      )}

      {error && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--danger)' }}>
          Error: {error}
        </div>
      )}

      {!loading && !error && managers.length === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
          No managers found.
        </div>
      )}

      {!loading && managers.length > 0 && (
        <>
          {/* Filter Controls */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem',
            marginBottom: '2rem',
            alignItems: 'center'
          }}>
            {/* Filter Buttons */}
            <div style={{
              display: 'flex',
              gap: '0.75rem',
              flexWrap: 'wrap',
              justifyContent: 'center'
            }}>
              {filterOptions.map(option => (
                <button
                  key={option.key}
                  onClick={() => setFilterActive(option.key)}
                  style={{
                    padding: '0.6rem 1.25rem',
                    background: filterActive === option.key
                      ? 'var(--accent)'
                      : 'var(--bg-alt)',
                    color: filterActive === option.key
                      ? 'white'
                      : 'var(--text)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}
                  onMouseEnter={(e) => {
                    if (filterActive !== option.key) {
                      e.currentTarget.style.background = 'var(--bg)';
                      e.currentTarget.style.borderColor = 'var(--accent)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (filterActive !== option.key) {
                      e.currentTarget.style.background = 'var(--bg-alt)';
                      e.currentTarget.style.borderColor = 'var(--border)';
                    }
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {/* Results count */}
            <div style={{
              fontSize: '0.85rem',
              color: 'var(--muted)',
              fontStyle: 'italic'
            }}>
              Showing {sortedManagers.length} {sortedManagers.length === 1 ? 'manager' : 'managers'}
            </div>
          </div>

          {/* Manager Cards - Full Width Stack */}
          {sortedManagers.length > 0 && (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              maxWidth: '1400px',
              margin: '0 auto'
            }}>
              {sortedManagers.map((manager, i) => (
                <ManagerCard key={i} manager={manager} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
