import React, { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useManagersList } from '../hooks/useManagersList';

/**
 * ManagersPage - Card-based grid view of all managers
 *
 * URL SYNC PATTERN:
 * - Filter changes create new history entries (no replace: true)
 * - Back button undoes filter changes
 * - URL params sync bidirectionally with component state
 */
export default function ManagersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filterActive, setFilterActive] = useState('active'); // 'all' or 'active'

  // Track if we're syncing from URL to prevent loops
  const isSyncingFromUrlRef = useRef(false);

  // Sync state from URL params (runs on mount and when URL changes via back/forward)
  useEffect(() => {
    isSyncingFromUrlRef.current = true;

    const filterParam = searchParams.get('filter');
    setFilterActive(filterParam === 'all' ? 'all' : 'active');

    // Reset flag after state updates have been processed
    setTimeout(() => {
      isSyncingFromUrlRef.current = false;
    }, 0);
  }, [searchParams]);

  // Update URL when filter changes from user interaction
  useEffect(() => {
    if (isSyncingFromUrlRef.current) return;

    const params = new URLSearchParams();
    if (filterActive === 'all') {
      params.set('filter', 'all');
    }
    // Don't set param for 'active' - it's the default

    setSearchParams(params); // No replace: true - creates new history entries
  }, [filterActive, setSearchParams]);

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
    { key: 'active', label: 'Active Managers' },
    { key: 'all', label: 'All Time Managers' }
  ];

  // Determine rank color based on dynamic thirds
  const getRankCircleColor = (r, w) => {
    if (!r || !w) return 'var(--text)';
    const firstThird = Math.ceil(w / 3);
    const secondThird = Math.ceil((2 * w) / 3);

    if (r <= firstThird) return 'var(--success)';
    if (r <= secondThird) return 'var(--muted)';
    return 'var(--danger)';
  };

  // Helper function to format years active
  const formatYearsActive = (years) => {
    if (!years || years.length === 0) return { yearsText: 'N/A', seasonsText: null };
    if (years.length === 1) return { yearsText: years[0], seasonsText: '(1 season)' };

    const sortedYears = [...years].map(y => Number(y)).sort((a, b) => a - b);
    const first = sortedYears[0];
    const last = sortedYears[sortedYears.length - 1];
    const count = sortedYears.length;

    // Check if years are continuous
    const isContinuous = sortedYears.every((year, i) => {
      if (i === 0) return true;
      return year === sortedYears[i - 1] + 1;
    });

    if (isContinuous) {
      return {
        yearsText: `${first}-${last}`,
        seasonsText: `(${count} season${count !== 1 ? 's' : ''})`
      };
    } else {
      return {
        yearsText: sortedYears.join(', '),
        seasonsText: `(${count} season${count !== 1 ? 's' : ''})`
      };
    }
  };

  return (
    <div className="App" style={{ paddingTop: '1.5rem' }}>
      {/* Page Header */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginBottom: '2rem'
      }}>
        <h1 style={{
          margin: 0,
          fontWeight: 700,
          fontSize: '2.5rem',
          letterSpacing: '1px'
        }}>
          Managers
        </h1>
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
          <div style={{
            maxWidth: '1400px',
            margin: '0 auto'
          }}>
            {/* Filter Tabs */}
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              borderBottom: '1px solid var(--border)',
              marginBottom: '1.5rem'
            }}>
              {filterOptions.map(option => (
                <button
                  key={option.key}
                  onClick={() => setFilterActive(option.key)}
                  style={{
                    padding: '0.75rem 1.5rem',
                    background: 'none',
                    border: 'none',
                    borderBottom: filterActive === option.key ? '2px solid var(--accent)' : '2px solid transparent',
                    color: filterActive === option.key ? 'var(--accent)' : 'var(--text)',
                    cursor: 'pointer',
                    fontSize: '1rem',
                    fontWeight: filterActive === option.key ? 600 : 400,
                    transition: 'all 0.2s ease',
                    whiteSpace: 'nowrap'
                  }}
                  onMouseEnter={(e) => {
                    if (filterActive !== option.key) {
                      e.currentTarget.style.color = 'var(--accent)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (filterActive !== option.key) {
                      e.currentTarget.style.color = 'var(--text)';
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
              fontStyle: 'italic',
              textAlign: 'center',
              marginBottom: '2rem'
            }}>
              Showing {sortedManagers.length} {sortedManagers.length === 1 ? 'manager' : 'managers'}
            </div>

            {/* Manager Cards - Two Column Grid */}
            {sortedManagers.length > 0 && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: '1rem'
              }}>
              {sortedManagers.map((manager, i) => {
                const {
                  name,
                  image_url,
                  years_active = [],
                  wins = 0,
                  losses = 0,
                  ties = 0,
                  win_percentage = 0,
                  playoff_appearances = 0,
                  best_finish = null,
                  total_trades = 0,
                  total_adds = 0,
                  total_drops = 0,
                  average_points_for = 0,
                  is_active = true,
                  rankings = {},
                  placements = {}
                } = manager;

                const recordString = ties > 0 ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`;
                const { yearsText, seasonsText } = formatYearsActive(years_active);

                const medalCounts = {
                  gold: placements.first_place || 0,
                  silver: placements.second_place || 0,
                  bronze: placements.third_place || 0
                };

                const isChampion = medalCounts.gold > 0;

                const goldColor = '#C9A433';

                return (
                  <Link
                    key={i}
                    to={`/manager/${encodeURIComponent(name)}`}
                    style={{
                      border: '1px solid var(--border)',
                      borderRadius: '8px',
                      overflow: 'hidden',
                      width: '100%',
                      background: 'var(--card-bg)',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      minHeight: '140px',
                      textDecoration: 'none',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = 'var(--bg)';
                      if (!isChampion) {
                        e.currentTarget.style.borderColor = 'var(--accent)';
                      }
                      if (isChampion) {
                        e.currentTarget.style.boxShadow = `0 0 12px ${goldColor}`;
                      } else {
                        e.currentTarget.style.boxShadow = '0 0 12px var(--accent)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'var(--card-bg)';
                      if (!isChampion) {
                        e.currentTarget.style.borderColor = 'var(--border)';
                      }
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    {/* Left Section: Image, Name, Years, Record */}
                    <div style={{
                      padding: '0.75rem',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.375rem',
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRight: '1px solid var(--border)',
                      minWidth: '150px',
                      flexShrink: 0
                    }}>
                      {/* Profile Picture with Medal */}
                      <div style={{ position: 'relative', marginBottom: '0.75rem' }}>
                        <div style={{
                          width: '105px',
                          height: '105px',
                          borderRadius: '50%',
                          border: '3px solid var(--border)',
                          background: 'var(--bg-alt)',
                          overflow: 'hidden',
                          transition: 'border-color 0.2s ease',
                          boxShadow: isChampion ? `0 0 20px ${goldColor}` : 'none'
                        }}>
                          {image_url && (
                            <img
                              src={image_url}
                              alt={name}
                              style={{
                                width: '100%',
                                height: '100%',
                                objectFit: 'cover'
                              }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          )}
                        </div>

                        {/* Medal hanging off bottom */}
                        {(medalCounts.gold > 0 || medalCounts.silver > 0 || medalCounts.bronze > 0) && (
                          <div style={{
                            position: 'absolute',
                            bottom: '-8px',
                            left: '50%',
                            transform: 'translateX(-50%)',
                            display: 'flex',
                            gap: '0.375rem',
                            background: 'var(--bg)',
                            padding: '0.375rem 0.5rem',
                            borderRadius: '15px',
                            border: '1.5px solid var(--border)',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                          }}>
                            {medalCounts.gold > 0 && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                                <span style={{ fontSize: '0.95rem' }}>🥇</span>
                                <span style={{ fontSize: '0.7rem', fontWeight: 700, opacity: 0.85, color: 'var(--text)' }}>×{medalCounts.gold}</span>
                              </div>
                            )}
                            {medalCounts.silver > 0 && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                                <span style={{ fontSize: '0.95rem' }}>🥈</span>
                                <span style={{ fontSize: '0.7rem', fontWeight: 700, opacity: 0.85, color: 'var(--text)' }}>×{medalCounts.silver}</span>
                              </div>
                            )}
                            {medalCounts.bronze > 0 && (
                              <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                                <span style={{ fontSize: '0.95rem' }}>🥉</span>
                                <span style={{ fontSize: '0.7rem', fontWeight: 700, opacity: 0.85, color: 'var(--text)' }}>×{medalCounts.bronze}</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Manager Name */}
                      <div style={{
                        margin: '0.375rem 0 0.375rem 0',
                        fontSize: '1.5rem',
                        fontWeight: 700,
                        color: isChampion ? goldColor : 'var(--text)',
                        textAlign: 'center',
                        textShadow: isChampion ? '0 0 8px rgba(201, 164, 51, 0.5)' : 'none'
                      }}>
                        {name}
                      </div>

                      {/* Years Active */}
                      <div style={{
                        color: 'var(--muted)',
                        fontSize: '0.71rem',
                        textAlign: 'center',
                        marginBottom: '0.375rem'
                      }}>
                        {yearsText}
                      </div>
                      {seasonsText && (
                        <div style={{
                          color: 'var(--muted)',
                          fontSize: '0.71rem',
                          textAlign: 'center'
                        }}>
                          {seasonsText}
                        </div>
                      )}

                      {/* Record */}
                      <div style={{
                        color: 'var(--text)',
                        fontSize: '1.125rem',
                        fontWeight: 700,
                        textAlign: 'center'
                      }}>
                        {recordString}
                      </div>

                      {/* Inactive label */}
                      {!is_active && (
                        <div style={{
                          fontSize: '0.525rem',
                          color: 'var(--muted)',
                          fontStyle: 'italic',
                          marginTop: '0.2rem'
                        }}>
                          (Inactive)
                        </div>
                      )}
                    </div>

                    {/* Right Section: Stats */}
                    <div style={{
                      flex: 1,
                      padding: '1rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.5rem'
                    }}>
                      {/* Top Section - 1/3 space: Seasons, Best, Adds, Drops */}
                      <div style={{
                        flex: 1,
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '0.5rem 1.5rem',
                        alignItems: 'start'
                      }}>
                        <div style={{
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Seasons</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)' }}>
                            {years_active.length}
                          </div>
                        </div>

                        {best_finish && (
                          <div style={{
                            textAlign: 'center',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '0.25rem'
                          }}>
                            <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Best Finish</div>
                            <div style={{
                              fontSize: '1.25rem',
                              fontWeight: 700,
                              color: best_finish === 1 ? goldColor
                                    : best_finish === 2 ? '#909090'
                                    : best_finish === 3 ? '#CD7F32'
                                    : (best_finish === 'Never Made Playoffs' || best_finish === 'N/A') ? 'var(--danger)'
                                    : 'var(--text)',
                              textShadow: best_finish === 1 ? '0 0 8px rgba(201, 164, 51, 0.5)'
                                        : best_finish === 2 ? '0 0 8px rgba(192, 192, 192, 0.5)'
                                        : best_finish === 3 ? '0 0 8px rgba(205, 127, 50, 0.5)'
                                        : 'none'
                            }}>
                              {typeof best_finish === 'number'
                                ? (best_finish === 1 ? '1st' : best_finish === 2 ? '2nd' : best_finish === 3 ? '3rd' : `${best_finish}th`)
                                : best_finish === 'Never Made Playoffs' ? 'N/A' : best_finish}
                            </div>
                          </div>
                        )}

                        <div style={{
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Adds</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)' }}>
                            {total_adds}
                          </div>
                        </div>

                        <div style={{
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Drops</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)' }}>
                            {total_drops}
                          </div>
                        </div>
                      </div>

                      {/* Bottom Section - 2/3 space: Win %, PPG, Playoffs, Trades with rank circles below */}
                      <div style={{
                        flex: 2,
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '1rem 1.5rem',
                        alignItems: 'start'
                      }}>
                        {/* Win % */}
                        <div style={{
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Win %</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankCircleColor(rankings.win_percentage, rankings.worst), opacity: 0.85 }}>
                            {win_percentage.toFixed(1)}%
                          </div>
                          {rankings.win_percentage && rankings.worst && (
                            <div style={{
                              width: '24px',
                              height: '24px',
                              borderRadius: '50%',
                              background: getRankCircleColor(rankings.win_percentage, rankings.worst),
                              color: '#000000',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {rankings.win_percentage}
                            </div>
                          )}
                        </div>

                        {/* PPG */}
                        <div style={{
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>PPG</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankCircleColor(rankings.average_points_for, rankings.worst), opacity: 0.85 }}>
                            {average_points_for.toFixed(1)}
                          </div>
                          {rankings.average_points_for && rankings.worst && (
                            <div style={{
                              width: '24px',
                              height: '24px',
                              borderRadius: '50%',
                              background: getRankCircleColor(rankings.average_points_for, rankings.worst),
                              color: '#000000',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {rankings.average_points_for}
                            </div>
                          )}
                        </div>

                        {/* Playoffs */}
                        <div style={{
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Playoffs</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankCircleColor(rankings.playoffs, rankings.worst), opacity: 0.85 }}>
                            {playoff_appearances}
                          </div>
                          {rankings.playoffs && rankings.worst && (
                            <div style={{
                              width: '24px',
                              height: '24px',
                              borderRadius: '50%',
                              background: getRankCircleColor(rankings.playoffs, rankings.worst),
                              color: '#000000',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {rankings.playoffs}
                            </div>
                          )}
                        </div>

                        {/* Trades */}
                        <div style={{
                          textAlign: 'center',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <div style={{ fontSize: '0.65rem', color: 'var(--muted)', textTransform: 'uppercase' }}>Trades</div>
                          <div style={{ fontSize: '1.25rem', fontWeight: 700, color: getRankCircleColor(rankings.trades, rankings.worst), opacity: 0.85 }}>
                            {total_trades}
                          </div>
                          {rankings.trades && rankings.worst && (
                            <div style={{
                              width: '24px',
                              height: '24px',
                              borderRadius: '50%',
                              background: getRankCircleColor(rankings.trades, rankings.worst),
                              color: '#000000',
                              fontSize: '0.75rem',
                              fontWeight: 700,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center'
                            }}>
                              {rankings.trades}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
          </div>
        </>
      )}
    </div>
  );
}
