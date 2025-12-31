import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useHeadToHead } from '../hooks/useHeadToHead';
import { MatchupCard } from '../components/MatchupCard';
import { TradeCard } from '../components/TradeCard';

/**
 * HeadToHeadPage - Clean, flowing head-to-head rivalry page
 * Minimal boxes, clean aesthetic inspired by Overview page
 *
 * URL SYNC PATTERN:
 * - Tab changes create new history entries (no replace: true)
 * - Back button undoes tab changes
 * - URL params sync bidirectionally with component state
 */
export default function HeadToHeadPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const manager1 = searchParams.get('manager1');
  const manager2 = searchParams.get('manager2');
  const year = searchParams.get('year');

  const { data, loading, error } = useHeadToHead(manager1, manager2, { year });
  const [activeTab, setActiveTab] = useState('matchups');

  // Track if we're syncing from URL to prevent loops
  const isSyncingFromUrlRef = useRef(false);

  // Sync state from URL params (runs on mount and when URL changes via back/forward)
  useEffect(() => {
    isSyncingFromUrlRef.current = true;

    const tabParam = searchParams.get('tab');
    const validTabs = ['matchups', 'trades'];
    setActiveTab(validTabs.includes(tabParam) ? tabParam : 'matchups');

    // Reset flag after state updates have been processed
    setTimeout(() => {
      isSyncingFromUrlRef.current = false;
    }, 0);
  }, [searchParams]);

  // Update URL when tab changes from user interaction
  useEffect(() => {
    if (isSyncingFromUrlRef.current) return;

    const params = new URLSearchParams();
    // Preserve existing params
    if (manager1) params.set('manager1', manager1);
    if (manager2) params.set('manager2', manager2);
    if (year) params.set('year', year);

    // Add tab param if not default
    if (activeTab !== 'matchups') {
      params.set('tab', activeTab);
    }
    // Don't set param for 'matchups' - it's the default

    setSearchParams(params); // No replace: true - creates new history entries
  }, [activeTab, manager1, manager2, year, setSearchParams]);

  if (!manager1 || !manager2) {
    return (
      <div className="App" style={{ paddingTop: '2rem' }}>
        <p style={{ color: 'var(--danger)' }}>Please provide both manager1 and manager2 as URL parameters.</p>
      </div>
    );
  }

  if (loading && !data) {
    return (
      <div className="App" style={{ paddingTop: '2rem' }}>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="App" style={{ paddingTop: '2rem' }}>
        <p style={{ color: 'var(--danger)' }}>Error: {error}</p>
      </div>
    );
  }

  if (!data) return null;

  const m1 = data.manager_1 || {};
  const m2 = data.manager_2 || {};
  const overall = data.overall || {};
  const tradesData = data.trades_between || {};

  // Check multiple possible locations for matchup history
  const matchupHistory = data.matchup_history || overall.matchup_history || data.matchups || [];

  const m1Key = m1.name?.toLowerCase().replace(/\s+/g, '_');
  const m2Key = m2.name?.toLowerCase().replace(/\s+/g, '_');

  const m1Wins = overall[`${m1Key}_wins`] || 0;
  const m2Wins = overall[`${m2Key}_wins`] || 0;
  const ties = overall.ties || 0;
  const totalGames = m1Wins + m2Wins + ties;

  const m1PointsFor = overall[`${m1Key}_points_for`] || 0;
  const m2PointsFor = overall[`${m2Key}_points_for`] || 0;

  const m1AvgMargin = overall[`${m1Key}_average_margin_of_victory`] || 0;
  const m2AvgMargin = overall[`${m2Key}_average_margin_of_victory`] || 0;

  const m1LastWin = overall[`${m1Key}_last_win`] || null;
  const m2LastWin = overall[`${m2Key}_last_win`] || null;

  const m1BiggestBlowout = overall[`${m1Key}_biggest_blowout`] || null;
  const m2BiggestBlowout = overall[`${m2Key}_biggest_blowout`] || null;

  const totalTrades = tradesData.total || 0;
  const tradeHistory = tradesData.trade_history || [];

  const m1WinPct = totalGames > 0 ? ((m1Wins / totalGames) * 100).toFixed(1) : '0.0';
  const m2WinPct = totalGames > 0 ? ((m2Wins / totalGames) * 100).toFixed(1) : '0.0';

  return (
    <div className="App" style={{ paddingTop: '1rem' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Five-column layout */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1.5fr auto 1.5fr 1fr',
          gap: '1rem',
          marginBottom: '1.5rem',
          paddingBottom: '1rem',
          alignItems: 'center'
        }}>
          {/* Column 1 - Manager 1 Stats */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            textAlign: 'left'
          }}>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Wins
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: m1Wins > m2Wins ? 'var(--success)' : 'var(--text)'
              }}>
                {m1Wins}
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Win %
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: 'var(--text)'
              }}>
                {m1WinPct}%
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Avg Win Margin
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: m1AvgMargin > m2AvgMargin ? 'var(--success)' : 'var(--text)'
              }}>
                {m1AvgMargin.toFixed(1)}
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Avg PTS/Game
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: (m1PointsFor / totalGames) > (m2PointsFor / totalGames) ? 'var(--success)' : 'var(--text)'
              }}>
                {(totalGames > 0 ? m1PointsFor / totalGames : 0).toFixed(1)}
              </div>
            </div>
          </div>

          {/* Column 2 - Manager 1 Image and Name */}
          <Link
            to={`/manager/${encodeURIComponent(m1.name)}`}
            style={{
              textDecoration: 'none',
              display: 'inline-flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1rem',
              border: '1px solid transparent',
              background: 'transparent',
              borderRadius: '8px',
              transition: 'all 0.2s ease',
              cursor: 'pointer',
              boxSizing: 'border-box',
              padding: '0.5rem'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg)';
              e.currentTarget.style.borderColor = 'var(--accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.borderColor = 'transparent';
            }}
          >
            {m1.image_url && (
              <img
                src={m1.image_url}
                alt={m1.name}
                style={{
                  width: '150px',
                  height: '150px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '4px solid var(--border)',
                  boxShadow: m1Wins > m2Wins ? '0 0 20px rgba(46, 204, 113, 0.3)' : 'none'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
            <div style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--text)',
              textAlign: 'center'
            }}>
              {m1.name}
            </div>
          </Link>

          {/* Column 3 - VS with counts */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <div style={{
              width: '150px',
              height: '150px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <div style={{
                fontSize: '3rem',
                fontWeight: 700,
                color: 'var(--muted)'
              }}>
                vs
              </div>
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <div style={{
                fontSize: '1.2rem',
                fontWeight: 700,
                textTransform: 'uppercase'
              }}>
                <span style={{ color: 'var(--text)' }}>{totalGames}</span>
                {' '}
                <span style={{ color: 'var(--muted)' }}>games</span>
              </div>
              <div style={{
                fontSize: '1.2rem',
                fontWeight: 700,
                textTransform: 'uppercase'
              }}>
                <span style={{ color: 'var(--text)' }}>{totalTrades}</span>
                {' '}
                <span style={{ color: 'var(--muted)' }}>trades</span>
              </div>
            </div>
          </div>

          {/* Column 4 - Manager 2 Image and Name */}
          <Link
            to={`/manager/${encodeURIComponent(m2.name)}`}
            style={{
              textDecoration: 'none',
              display: 'inline-flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '1rem',
              border: '1px solid transparent',
              background: 'transparent',
              borderRadius: '8px',
              transition: 'all 0.2s ease',
              cursor: 'pointer',
              boxSizing: 'border-box',
              padding: '0.5rem'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg)';
              e.currentTarget.style.borderColor = 'var(--accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.borderColor = 'transparent';
            }}
          >
            {m2.image_url && (
              <img
                src={m2.image_url}
                alt={m2.name}
                style={{
                  width: '150px',
                  height: '150px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '4px solid var(--border)',
                  boxShadow: m2Wins > m1Wins ? '0 0 20px rgba(46, 204, 113, 0.3)' : 'none'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
            <div style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--text)',
              textAlign: 'center'
            }}>
              {m2.name}
            </div>
          </Link>

          {/* Column 5 - Manager 2 Stats */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1rem',
            textAlign: 'right'
          }}>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Wins
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: m2Wins > m1Wins ? 'var(--success)' : 'var(--text)'
              }}>
                {m2Wins}
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Win %
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: 'var(--text)'
              }}>
                {m2WinPct}%
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Avg Win Margin
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: m2AvgMargin > m1AvgMargin ? 'var(--success)' : 'var(--text)'
              }}>
                {m2AvgMargin.toFixed(1)}
              </div>
            </div>
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 600,
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '0.25rem'
              }}>
                Avg PTS/Game
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                color: (m2PointsFor / totalGames) > (m1PointsFor / totalGames) ? 'var(--success)' : 'var(--text)'
              }}>
                {(totalGames > 0 ? m2PointsFor / totalGames : 0).toFixed(1)}
              </div>
            </div>
          </div>
        </div>

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        marginBottom: '2rem',
        borderBottom: '2px solid var(--border)',
        justifyContent: 'center'
      }}>
        <button
          onClick={() => setActiveTab('matchups')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            fontWeight: activeTab === 'matchups' ? 600 : 400,
            color: activeTab === 'matchups' ? 'var(--accent)' : 'var(--text)',
            cursor: 'pointer',
            borderBottom: activeTab === 'matchups' ? '2px solid var(--accent)' : '2px solid transparent',
            marginBottom: '-2px',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap'
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'matchups') {
              e.currentTarget.style.color = 'var(--accent)';
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'matchups') {
              e.currentTarget.style.color = 'var(--text)';
            }
          }}
        >
          {year ? `${year} Matchups` : 'All Matchups'} ({matchupHistory.length})
        </button>
        <button
          onClick={() => setActiveTab('trades')}
          style={{
            background: 'none',
            border: 'none',
            padding: '0.75rem 1.5rem',
            fontSize: '1rem',
            fontWeight: activeTab === 'trades' ? 600 : 400,
            color: activeTab === 'trades' ? 'var(--accent)' : 'var(--text)',
            cursor: 'pointer',
            borderBottom: activeTab === 'trades' ? '2px solid var(--accent)' : '2px solid transparent',
            marginBottom: '-2px',
            transition: 'all 0.2s ease',
            whiteSpace: 'nowrap'
          }}
          onMouseEnter={(e) => {
            if (activeTab !== 'trades') {
              e.currentTarget.style.color = 'var(--accent)';
            }
          }}
          onMouseLeave={(e) => {
            if (activeTab !== 'trades') {
              e.currentTarget.style.color = 'var(--text)';
            }
          }}
        >
          {year ? `${year} Trades` : 'All Trades'} ({totalTrades})
        </button>
      </div>

      {/* Matchups Tab */}
      {activeTab === 'matchups' && (
        <div style={{ marginBottom: '3rem', minHeight: '400px' }}>
          {matchupHistory.length > 0 ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '1.5rem',
              alignItems: 'center'
            }}>
              {matchupHistory.map((matchup, idx) => {
                // Check if this matchup is notable
                const isM1LastWin = m1LastWin && matchup.week === m1LastWin.week && matchup.year === m1LastWin.year;
                const isM2LastWin = m2LastWin && matchup.week === m2LastWin.week && matchup.year === m2LastWin.year;
                const isM1BiggestBlowout = m1BiggestBlowout && matchup.week === m1BiggestBlowout.week && matchup.year === m1BiggestBlowout.year;
                const isM2BiggestBlowout = m2BiggestBlowout && matchup.week === m2BiggestBlowout.week && matchup.year === m2BiggestBlowout.year;

                // Collect all applicable labels
                const notableLabels = [];
                if (isM1LastWin) notableLabels.push(`${m1.name}'s Last Win`);
                if (isM2LastWin) notableLabels.push(`${m2.name}'s Last Win`);
                if (isM1BiggestBlowout) notableLabels.push(`${m1.name}'s Biggest Blowout`);
                if (isM2BiggestBlowout) notableLabels.push(`${m2.name}'s Biggest Blowout`);

                const isNotable = notableLabels.length > 0;

                return (
                  <div key={idx}>
                    {notableLabels.map((label, labelIdx) => (
                      <div key={labelIdx} style={{
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        color: 'var(--accent)',
                        marginBottom: '0.5rem',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        {label}
                      </div>
                    ))}
                    <div style={{
                      boxShadow: isNotable ? '0 0 20px rgba(52, 152, 219, 0.4)' : 'none',
                      borderRadius: '8px'
                    }}>
                      <MatchupCard matchup={matchup} showMargin={isM1BiggestBlowout || isM2BiggestBlowout} />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '3rem',
              fontSize: '1.2rem',
              color: 'var(--muted)'
            }}>
              No Matchups
            </div>
          )}
        </div>
      )}

      {/* Trades Tab */}
      {activeTab === 'trades' && (
        <div style={{ marginBottom: '3rem', minHeight: '400px' }}>
          {tradeHistory.length > 0 ? (
            <>
              {/* Render trades chronologically with adaptive layout */}
              {(() => {
                const elements = [];
                let twoManagerBatch = [];

                tradeHistory.forEach((trade, idx) => {
                  const managerCount = (trade.managers_involved || []).length;

                  if (managerCount === 2) {
                    // Accumulate 2-manager trades
                    twoManagerBatch.push({ trade, originalIdx: idx });
                  } else {
                    // Flush any accumulated 2-manager trades before rendering 3+ manager trade
                    if (twoManagerBatch.length > 0) {
                      const hasOddNumber = twoManagerBatch.length % 2 === 1;

                      if (hasOddNumber) {
                        // Render all but the last trade in a grid
                        const allButLast = twoManagerBatch.slice(0, -1);
                        const lastTrade = twoManagerBatch[twoManagerBatch.length - 1];

                        if (allButLast.length > 0) {
                          elements.push(
                            <div key={`batch-${elements.length}`} style={{
                              display: 'grid',
                              gridTemplateColumns: 'repeat(2, 1fr)',
                              gap: '1.5rem',
                              marginBottom: '1.5rem'
                            }}>
                              {allButLast.map((item) => (
                                <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} />
                              ))}
                            </div>
                          );
                        }

                        // Center the last trade
                        elements.push(
                          <div key={`batch-${elements.length}`} style={{
                            display: 'flex',
                            justifyContent: 'center',
                            marginBottom: '1.5rem'
                          }}>
                            <div style={{ width: '50%' }}>
                              <TradeCard key={`2m-${lastTrade.originalIdx}`} trade={lastTrade.trade} hideHeader={false} />
                            </div>
                          </div>
                        );
                      } else {
                        elements.push(
                          <div key={`batch-${elements.length}`} style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(2, 1fr)',
                            gap: '1.5rem',
                            marginBottom: '1.5rem'
                          }}>
                            {twoManagerBatch.map((item) => (
                              <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} />
                            ))}
                          </div>
                        );
                      }
                      twoManagerBatch = [];
                    }

                    // Render the 3+ manager trade at full width
                    elements.push(
                      <div key={`3m-${idx}`} style={{ marginBottom: '1.5rem' }}>
                        <TradeCard trade={trade} hideHeader={false} />
                      </div>
                    );
                  }
                });

                // Flush any remaining 2-manager trades at the end
                if (twoManagerBatch.length > 0) {
                  const hasOddNumber = twoManagerBatch.length % 2 === 1;

                  if (hasOddNumber) {
                    // Render all but the last trade in a grid
                    const allButLast = twoManagerBatch.slice(0, -1);
                    const lastTrade = twoManagerBatch[twoManagerBatch.length - 1];

                    if (allButLast.length > 0) {
                      elements.push(
                        <div key={`batch-${elements.length}`} style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(2, 1fr)',
                          gap: '1.5rem',
                          marginBottom: '1.5rem'
                        }}>
                          {allButLast.map((item) => (
                            <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} />
                          ))}
                        </div>
                      );
                    }

                    // Center the last trade
                    elements.push(
                      <div key={`batch-${elements.length}`} style={{
                        display: 'flex',
                        justifyContent: 'center'
                      }}>
                        <div style={{ width: '50%' }}>
                          <TradeCard key={`2m-${lastTrade.originalIdx}`} trade={lastTrade.trade} hideHeader={false} />
                        </div>
                      </div>
                    );
                  } else {
                    elements.push(
                      <div key={`batch-${elements.length}`} style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: '1.5rem'
                      }}>
                        {twoManagerBatch.map((item) => (
                          <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} />
                        ))}
                      </div>
                    );
                  }
                }

                return elements;
              })()}
            </>
          ) : (
            <div style={{
              textAlign: 'center',
              padding: '3rem',
              fontSize: '1.2rem',
              color: 'var(--muted)'
            }}>
              No Trades
            </div>
          )}
        </div>
      )}
      </div>
    </div>
  );
}
