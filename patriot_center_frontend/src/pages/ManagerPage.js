import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useManagerSummary } from '../hooks/useManagerSummary';
import { useManagerAwards } from '../hooks/useManagerAwards';
import { useManagerTransactions } from '../hooks/useManagerTransactions';
import { useAggregatedPlayers } from '../hooks/useAggregatedPlayers';
import { MatchupCard } from '../components/MatchupCard';
import { TradeCard } from '../components/TradeCard';
import { WaiverCard } from '../components/WaiverCard';

/**
 * ManagerPage - Social media style profile view with ALL manager data
 *
 * URL SYNC PATTERN:
 * - Tab changes create new history entries (no replace: true)
 * - Back button undoes tab changes
 * - URL params sync bidirectionally with component state
 */
export default function ManagerPage() {
  const { managerName } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const [year] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // Track if we're syncing from URL to prevent loops
  const isSyncingFromUrlRef = useRef(false);

  // Responsive window width tracking
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Sync state from URL params (runs on mount and when URL changes via back/forward)
  useEffect(() => {
    isSyncingFromUrlRef.current = true;

    const tabParam = searchParams.get('tab');
    const validTabs = ['overview', 'trades', 'adds-drops'];
    setActiveTab(validTabs.includes(tabParam) ? tabParam : 'overview');

    // Reset flag after state updates have been processed
    setTimeout(() => {
      isSyncingFromUrlRef.current = false;
    }, 0);
  }, [searchParams]);

  // Update URL when tab changes from user interaction
  useEffect(() => {
    if (isSyncingFromUrlRef.current) return;

    const params = new URLSearchParams();
    if (activeTab !== 'overview') {
      params.set('tab', activeTab);
    }
    // Don't set param for 'overview' - it's the default

    setSearchParams(params); // No replace: true - creates new history entries
  }, [activeTab, setSearchParams]);

  // Fetch data from ALL endpoints
  const { summary, loading: summaryLoading, error: summaryError } = useManagerSummary(managerName, { year });
  const { awards, loading: awardsLoading } = useManagerAwards(managerName);
  const { transactions: transactionHistory, loading: transactionsLoading } = useManagerTransactions(managerName);

  // Fetch aggregated players for top player cards (all years)
  const { players: aggregatedPlayers } = useAggregatedPlayers(null, null, managerName);

  // Calculate top players from aggregated data
  const topPlayers = React.useMemo(() => {
    if (!aggregatedPlayers || aggregatedPlayers.length === 0) {
      return { highest: null, lowest: null, mostStarted: null };
    }

    const highest = aggregatedPlayers.reduce((max, p) => (p.ffWAR || 0) > (max.ffWAR || 0) ? p : max, aggregatedPlayers[0]);
    const lowest = aggregatedPlayers.reduce((min, p) => (p.ffWAR || 0) < (min.ffWAR || 0) ? p : min, aggregatedPlayers[0]);
    const mostStarted = aggregatedPlayers.reduce((max, p) => {
      if ((p.num_games_started || 0) > (max.num_games_started || 0)) return p;
      if ((p.num_games_started || 0) === (max.num_games_started || 0) && (p.ffWAR || 0) > (max.ffWAR || 0)) return p;
      return max;
    }, aggregatedPlayers[0]);

    return { highest, lowest, mostStarted };
  }, [aggregatedPlayers]);

  React.useEffect(() => {
    setImageError(false);
  }, [managerName]);

  const loading = summaryLoading || awardsLoading || transactionsLoading;
  const error = summaryError;

  if (loading && !summary) return <div className="App" style={{ paddingTop: '2rem' }}><p>Loading manager data...</p></div>;
  if (error) return <div className="App" style={{ paddingTop: '2rem' }}><p style={{ color: 'var(--danger)' }}>Error: {error}</p></div>;
  if (!summary) return null;

  // Extract data
  const avatarUrl = summary.image_url;
  const yearsActive = summary.years_active || [];
  const overall = summary.matchup_data?.overall || {};
  const regularSeason = summary.matchup_data?.regular_season || {};
  const playoffs = summary.matchup_data?.playoffs || {};
  const transactions = summary.transactions || {};
  const trades = transactions.trades || {};
  const adds = transactions.adds || {};
  const drops = transactions.drops || {};
  const faab = transactions.faab || {};
  const overallData = summary.overall_data || {};
  const placements = overallData.placements || [];
  const playoffAppearances = overallData.playoff_appearances || 0;
  const rankings = summary.rankings || {};
  const isActiveManager = summary.rankings?.is_active_manager ?? true;
  const awardsData = awards?.awards || {};

  // Calculate medal counts
  const medalCounts = placements.reduce((acc, p) => {
    if (p.placement === 1) acc.gold++;
    else if (p.placement === 2) acc.silver++;
    else if (p.placement === 3) acc.bronze++;
    return acc;
  }, { gold: 0, silver: 0, bronze: 0 });

  const isChampion = medalCounts.gold > 0;
  const goldColor = '#C9A433';

  // Responsive breakpoints
  const isMobile = windowWidth < 768;

  return (
    <div className="App" style={{ paddingTop: 0, maxWidth: '1400px', margin: '0 auto' }}>
      {/* Profile Info Section */}
      <div style={{ padding: isMobile ? '1rem' : '2rem' }}>
        <div style={{
          display: 'flex',
          flexDirection: isMobile ? 'column' : 'row',
          gap: isMobile ? '1rem' : '2rem',
          marginBottom: '1rem',
          width: isMobile ? '100%' : '1000px',
          maxWidth: isMobile ? '100%' : '1000px',
          margin: '0 auto 1rem auto'
        }}>
          {/* Left - Profile Picture and Info */}
          <div style={{
            flex: isMobile ? '1' : '0 0 18%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            minWidth: 0
          }}>
            {/* Profile Picture with Medal */}
            <div style={{ position: 'relative', marginBottom: isMobile ? '0.75rem' : '1rem' }}>
              <div style={{
                width: isMobile ? '120px' : '140px',
                height: isMobile ? '120px' : '140px',
                borderRadius: '50%',
                border: isMobile ? '3px solid var(--border)' : '4px solid var(--border)',
                background: 'var(--bg-alt)',
                overflow: 'hidden',
                boxShadow: isChampion ? `0 0 20px ${goldColor}` : 'none'
              }}>
                {avatarUrl && !imageError && (
                  <img
                    src={avatarUrl}
                    alt={managerName}
                    onError={() => setImageError(true)}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                )}
              </div>

              {/* Medal hanging off bottom */}
              {(medalCounts.gold > 0 || medalCounts.silver > 0 || medalCounts.bronze > 0) && (
                <div style={{
                  position: 'absolute',
                  bottom: isMobile ? '-8px' : '-10px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  display: 'flex',
                  gap: isMobile ? '0.375rem' : '0.5rem',
                  background: 'var(--bg)',
                  padding: isMobile ? '0.375rem 0.5rem' : '0.5rem 0.75rem',
                  borderRadius: '20px',
                  border: '2px solid var(--border)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  {medalCounts.gold > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                      <span style={{ fontSize: isMobile ? '1rem' : '1.25rem' }}>🥇</span>
                      <span style={{ fontSize: isMobile ? '0.75rem' : '0.9rem', fontWeight: 700, opacity: 0.85 }}>×{medalCounts.gold}</span>
                    </div>
                  )}
                  {medalCounts.silver > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                      <span style={{ fontSize: isMobile ? '1rem' : '1.25rem' }}>🥈</span>
                      <span style={{ fontSize: isMobile ? '0.75rem' : '0.9rem', fontWeight: 700, opacity: 0.85 }}>×{medalCounts.silver}</span>
                    </div>
                  )}
                  {medalCounts.bronze > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                      <span style={{ fontSize: isMobile ? '1rem' : '1.25rem' }}>🥉</span>
                      <span style={{ fontSize: isMobile ? '0.75rem' : '0.9rem', fontWeight: 700, opacity: 0.85 }}>×{medalCounts.bronze}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Manager Info */}
            <h1 style={{
              margin: '0.5rem 0 0.5rem 0',
              fontSize: isMobile ? '1.75rem' : '2rem',
              textAlign: 'center',
              color: isChampion ? goldColor : 'var(--text)',
              textShadow: isChampion ? '0 0 8px rgba(201, 164, 51, 0.5)' : 'none'
            }}>{managerName}</h1>
            <div style={{ color: 'var(--muted)', fontSize: isMobile ? '0.85rem' : '0.95rem', marginBottom: '0.5rem', textAlign: 'center' }}>
              {formatYearsActive(yearsActive)}
            </div>
            <div style={{ color: 'var(--text)', fontSize: isMobile ? '1.25rem' : '1.5rem', fontWeight: 700, textAlign: 'center' }}>
              {formatRecord(overall.wins || 0, overall.losses || 0, overall.ties || 0)}
            </div>
          </div>

          {/* Vertical Divider */}
          {!isMobile && <div style={{ width: '1px', background: 'var(--border)', flexShrink: 0 }} />}

          {/* Mobile Tab Navigation - appears after manager info */}
          {isMobile && (
            <div style={{
              display: 'flex',
              gap: '0.25rem',
              borderBottom: '2px solid var(--border)',
              marginBottom: '1rem',
              overflowX: 'auto',
              justifyContent: 'center'
            }}>
              {[
                { id: 'overview', label: 'Overview' },
                { id: 'trades', label: `Trades${transactionHistory?.transactions ? ` (${transactionHistory.transactions.filter(t => t.type === 'trade').length})` : ''}` },
                { id: 'adds-drops', label: `Adds & Drops${transactionHistory?.transactions ? ` (${transactionHistory.transactions.filter(t => ['add', 'drop', 'add_and_drop'].includes(t.type)).length})` : ''}` }
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => !tab.disabled && setActiveTab(tab.id)}
                  disabled={tab.disabled}
                  style={{
                    padding: '0.5rem 0.75rem',
                    background: 'none',
                    border: 'none',
                    borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
                    color: tab.disabled ? 'var(--muted)' : activeTab === tab.id ? 'var(--accent)' : 'var(--text)',
                    cursor: tab.disabled ? 'not-allowed' : 'pointer',
                    fontSize: '0.85rem',
                    fontWeight: activeTab === tab.id ? 600 : 400,
                    transition: 'all 0.2s ease',
                    whiteSpace: 'nowrap',
                    opacity: tab.disabled ? 0.5 : 1
                  }}
                  onMouseEnter={(e) => {
                    if (!tab.disabled && activeTab !== tab.id) {
                      e.currentTarget.style.color = 'var(--accent)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!tab.disabled && activeTab !== tab.id) {
                      e.currentTarget.style.color = 'var(--text)';
                    }
                  }}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          )}

          {/* Right - Player Cards and Stats */}
          <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: isMobile ? '0.75rem' : '0.5rem', minWidth: 0, overflow: 'hidden' }}>
            {/* Top Half - Player Cards (desktop: always shown, mobile: only on overview tab) */}
            {(!isMobile || activeTab === 'overview') && (
              <div style={{
                flex: 1,
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: isMobile ? '0.5rem' : '1rem',
                alignContent: 'center',
                minWidth: 0
              }}>
                <PlayerStatCard
                  title="Highest ffWAR"
                  player={topPlayers.highest}
                  stat="ffWAR"
                  additionalInfo={topPlayers.highest ? `${topPlayers.highest.num_games_started} starts` : null}
                  isMobile={isMobile}
                />
                <PlayerStatCard
                  title="Lowest ffWAR"
                  player={topPlayers.lowest}
                  stat="ffWAR"
                  additionalInfo={topPlayers.lowest ? `${topPlayers.lowest.num_games_started} starts` : null}
                  isMobile={isMobile}
                />
                <PlayerStatCard
                  title="Most Started"
                  player={topPlayers.mostStarted}
                  stat="num_games_started"
                  additionalInfo={topPlayers.mostStarted ? `${topPlayers.mostStarted.ffWAR?.toFixed(3)} ffWAR` : null}
                  isMobile={isMobile}
                />
              </div>
            )}

            {/* Horizontal Divider (desktop: always shown, mobile: only on overview tab) */}
            {(!isMobile || activeTab === 'overview') && (
              <div style={{ height: '1px', background: 'var(--border)', margin: isMobile ? '0.5rem 0' : '0.5rem 0', maxWidth: '100%' }} />
            )}

            {/* Bottom Half - Stat Cards (desktop: always shown, mobile: only on overview tab) */}
            {(!isMobile || activeTab === 'overview') && (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: isMobile ? '0.75rem' : '0.5rem', justifyContent: 'center', maxWidth: '100%' }}>
                {rankings.worst && (
                  <div style={{
                    fontSize: isMobile ? '0.65rem' : '0.7rem',
                    color: 'var(--muted)',
                    textAlign: 'center',
                    letterSpacing: '0.3px'
                  }}>
                    {year
                      ? `Note: circle tiles reflect ranking among the ${rankings.worst} managers of the ${year} season`
                      : isActiveManager
                        ? `Note: circle tiles reflect ranking among the ${rankings.worst} active managers`
                        : `Note: circle tiles reflect ranking among the ${rankings.worst} managers all time`
                    }
                  </div>
                )}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: isMobile ? 'repeat(3, 1fr)' : 'repeat(6, 1fr)',
                  gap: isMobile ? '0.75rem' : '1rem'
                }}>
                  <RankedStatCard title="Win %" value={`${overall.win_percentage?.toFixed(1) || 0}%`} rank={rankings.win_percentage} worst={rankings.worst} isMobile={isMobile} />
                <RankedStatCard title="AVG PF" value={overall.average_points_for?.toFixed(2) || 0} rank={rankings.average_points_for} worst={rankings.worst} isMobile={isMobile} />
                <RankedStatCard title="AVG PA" value={overall.average_points_against?.toFixed(2) || 0} rank={rankings.average_points_against} worst={rankings.worst} isMobile={isMobile} />
                <RankedStatCard
                  title="AVG Diff"
                  value={overall.average_point_differential?.toFixed(2) || 0}
                  rank={rankings.average_points_differential}
                  worst={rankings.worst}
                  isMobile={isMobile}
                />
                <RankedStatCard title="Trades" value={trades.total || 0} rank={rankings.trades} worst={rankings.worst} isMobile={isMobile} />
                <RankedStatCard title="Playoffs" value={playoffAppearances} rank={rankings.playoffs} worst={rankings.worst} isMobile={isMobile} />
              </div>
            </div>
            )}
          </div>
        </div>
      </div>

      {/* Desktop Tab Navigation */}
      {!isMobile && <div style={{
        display: 'flex',
        gap: isMobile ? '0.25rem' : '0.5rem',
        borderBottom: '2px solid var(--border)',
        marginBottom: isMobile ? '1rem' : '2rem',
        width: isMobile ? '100%' : '1000px',
        maxWidth: isMobile ? '100%' : '1000px',
        margin: isMobile ? '0 auto 1rem auto' : '0 auto 2rem auto',
        overflowX: 'auto',
        justifyContent: 'center',
        padding: isMobile ? '0 0.5rem' : '0'
      }}>
          {[
            { id: 'overview', label: 'Overview' },
            {
              id: 'trades',
              label: `Trades${transactionHistory?.transactions ? ` (${transactionHistory.transactions.filter(t => t.type === 'trade').length})` : ''}`
            },
            {
              id: 'adds-drops',
              label: `Adds & Drops${transactionHistory?.transactions ? ` (${transactionHistory.transactions.filter(t => ['add', 'drop', 'add_and_drop'].includes(t.type)).length})` : ''}`
            }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              style={{
                padding: isMobile ? '0.5rem 0.75rem' : '0.75rem 1.5rem',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
                color: tab.disabled ? 'var(--muted)' : activeTab === tab.id ? 'var(--accent)' : 'var(--text)',
                cursor: tab.disabled ? 'not-allowed' : 'pointer',
                fontSize: isMobile ? '0.85rem' : '1rem',
                fontWeight: activeTab === tab.id ? 600 : 400,
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                opacity: tab.disabled ? 0.5 : 1
              }}
              onMouseEnter={(e) => {
                if (!tab.disabled && activeTab !== tab.id) {
                  e.currentTarget.style.color = 'var(--accent)';
                }
              }}
              onMouseLeave={(e) => {
                if (!tab.disabled && activeTab !== tab.id) {
                  e.currentTarget.style.color = 'var(--text)';
                }
              }}
            >
              {tab.label}
            </button>
          ))}
      </div>}

      {/* Tab Content */}
      <div style={{
        width: isMobile ? '100%' : '1000px',
        maxWidth: isMobile ? '100%' : '1000px',
        margin: '0 auto',
        padding: isMobile ? '0 1rem' : '0'
      }}>
        {activeTab === 'overview' && <OverviewTab
          overall={overall}
          regularSeason={regularSeason}
          playoffs={playoffs}
          trades={trades}
          adds={adds}
          drops={drops}
          faab={faab}
          placements={placements}
          headToHead={summary.head_to_head || {}}
          managerName={managerName}
          awardsData={awardsData}
          isMobile={isMobile}
        />}

        {activeTab === 'trades' && (
          <div style={{ marginBottom: '3rem', minHeight: '400px' }}>
            {transactionHistory && transactionHistory.transactions ? (
              (() => {
                const tradesData = transactionHistory.transactions.filter(t => t.type === 'trade');

                if (tradesData.length === 0) {
                  return (
                    <div style={{
                      textAlign: 'center',
                      padding: '3rem',
                      fontSize: '1.2rem',
                      color: 'var(--muted)'
                    }}>
                      No Trades
                    </div>
                  );
                }

                // Adaptive layout: 2-manager trades in 2-column grid, 3+ manager trades at full width
                const elements = [];
                let twoManagerBatch = [];

                tradesData.forEach((trade, idx) => {
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
                              gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                              gap: isMobile ? '1rem' : '1.5rem',
                              marginBottom: isMobile ? '1rem' : '1.5rem'
                            }}>
                              {allButLast.map((item) => (
                                <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} isMobile={isMobile} />
                              ))}
                            </div>
                          );
                        }

                        // Center the last trade
                        elements.push(
                          <div key={`batch-${elements.length}`} style={{
                            display: 'flex',
                            justifyContent: 'center',
                            marginBottom: isMobile ? '1rem' : '1.5rem'
                          }}>
                            <div style={{ width: isMobile ? '100%' : '50%' }}>
                              <TradeCard key={`2m-${lastTrade.originalIdx}`} trade={lastTrade.trade} hideHeader={false} isMobile={isMobile} />
                            </div>
                          </div>
                        );
                      } else {
                        elements.push(
                          <div key={`batch-${elements.length}`} style={{
                            display: 'grid',
                            gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                            gap: isMobile ? '1rem' : '1.5rem',
                            marginBottom: isMobile ? '1rem' : '1.5rem'
                          }}>
                            {twoManagerBatch.map((item) => (
                              <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} isMobile={isMobile} />
                            ))}
                          </div>
                        );
                      }
                      twoManagerBatch = [];
                    }

                    // Render the 3+ manager trade at full width
                    elements.push(
                      <div key={`3m-${idx}`} style={{ marginBottom: isMobile ? '1rem' : '1.5rem' }}>
                        <TradeCard trade={trade} hideHeader={false} isMobile={isMobile} />
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
                          gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                          gap: isMobile ? '1rem' : '1.5rem',
                          marginBottom: isMobile ? '1rem' : '1.5rem'
                        }}>
                          {allButLast.map((item) => (
                            <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} isMobile={isMobile} />
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
                        <div style={{ width: isMobile ? '100%' : '50%' }}>
                          <TradeCard key={`2m-${lastTrade.originalIdx}`} trade={lastTrade.trade} hideHeader={false} isMobile={isMobile} />
                        </div>
                      </div>
                    );
                  } else {
                    elements.push(
                      <div key={`batch-${elements.length}`} style={{
                        display: 'grid',
                        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, 1fr)',
                        gap: isMobile ? '1rem' : '1.5rem'
                      }}>
                        {twoManagerBatch.map((item) => (
                          <TradeCard key={`2m-${item.originalIdx}`} trade={item.trade} hideHeader={false} isMobile={isMobile} />
                        ))}
                      </div>
                    );
                  }
                }

                return elements;
              })()
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>Loading trades...</div>
            )}
          </div>
        )}

        {activeTab === 'adds-drops' && (
          <div style={{ marginBottom: '3rem', minHeight: '400px' }}>
            {transactionHistory && transactionHistory.transactions ? (
              (() => {
                const addsDropsData = transactionHistory.transactions.filter(t => ['add', 'drop', 'add_and_drop'].includes(t.type));

                if (addsDropsData.length === 0) {
                  return (
                    <div style={{
                      textAlign: 'center',
                      padding: '3rem',
                      fontSize: '1.2rem',
                      color: 'var(--muted)'
                    }}>
                      No Adds or Drops
                    </div>
                  );
                }

                // Group transactions by week and year
                const groupedByWeek = {};
                addsDropsData.forEach(txn => {
                  const key = `${txn.year}-W${txn.week}`;
                  if (!groupedByWeek[key]) {
                    groupedByWeek[key] = {
                      year: txn.year,
                      week: txn.week,
                      transactions: []
                    };
                  }
                  groupedByWeek[key].transactions.push(txn);
                });

                // Sort by year (desc) then week (desc)
                const sortedWeeks = Object.values(groupedByWeek).sort((a, b) => {
                  if (b.year !== a.year) return parseInt(b.year) - parseInt(a.year);
                  return parseInt(b.week) - parseInt(a.week);
                });

                // Group by year for rendering
                const groupedByYear = {};
                sortedWeeks.forEach(weekData => {
                  if (!groupedByYear[weekData.year]) {
                    groupedByYear[weekData.year] = [];
                  }
                  groupedByYear[weekData.year].push(weekData);
                });

                const years = Object.keys(groupedByYear).sort((a, b) => parseInt(b) - parseInt(a));

                return (
                  <div>
                    {years.map((year, yearIdx) => {
                      const yearWeeks = groupedByYear[year];
                      const hasOddNumber = yearWeeks.length % 2 === 1;

                      return (
                        <div key={year}>
                          {/* Year Separator */}
                          {yearIdx > 0 && (
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '1rem',
                              margin: '2rem 0 1.5rem 0'
                            }}>
                              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }}></div>
                              <div style={{
                                fontSize: '1.2rem',
                                fontWeight: 700,
                                letterSpacing: '1.5px',
                                textTransform: 'uppercase',
                                color: 'var(--text)'
                              }}>
                                {year}
                              </div>
                              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }}></div>
                            </div>
                          )}

                          {/* First year doesn't need top margin, just the label */}
                          {yearIdx === 0 && (
                            <div style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '1rem',
                              marginBottom: '1.5rem'
                            }}>
                              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }}></div>
                              <div style={{
                                fontSize: '1.2rem',
                                fontWeight: 700,
                                letterSpacing: '1.5px',
                                textTransform: 'uppercase',
                                color: 'var(--text)'
                              }}>
                                {year}
                              </div>
                              <div style={{ flex: 1, height: '1px', background: 'var(--border)' }}></div>
                            </div>
                          )}

                          {/* Render cards */}
                          {hasOddNumber ? (
                            <>
                              {/* All but last card in grid */}
                              {yearWeeks.length > 1 && (
                                <div style={{
                                  display: 'grid',
                                  gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(450px, 1fr))',
                                  gap: isMobile ? '1rem' : '1.5rem',
                                  justifyItems: 'center',
                                  marginBottom: isMobile ? '1rem' : '1.5rem'
                                }}>
                                  {yearWeeks.slice(0, -1).map((weekData, i) => (
                                    <WaiverCard key={i} weekData={weekData} isMobile={isMobile} />
                                  ))}
                                </div>
                              )}
                              {/* Last card centered */}
                              <div style={{
                                display: 'flex',
                                justifyContent: 'center'
                              }}>
                                <div style={{ width: isMobile ? '100%' : '450px', maxWidth: '100%' }}>
                                  <WaiverCard weekData={yearWeeks[yearWeeks.length - 1]} isMobile={isMobile} />
                                </div>
                              </div>
                            </>
                          ) : (
                            <div style={{
                              display: 'grid',
                              gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fill, minmax(450px, 1fr))',
                              gap: isMobile ? '1rem' : '1.5rem',
                              justifyItems: 'center'
                            }}>
                              {yearWeeks.map((weekData, i) => (
                                <WaiverCard key={i} weekData={weekData} isMobile={isMobile} />
                              ))}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })()
            ) : (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>Loading adds & drops...</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, color }) {
  return (
    <div style={{
      minWidth: '120px',
      padding: '1rem',
      background: 'var(--bg-alt)',
      borderRadius: '8px',
      border: '1px solid var(--border)',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>{title}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: color || 'var(--text)', opacity: 0.85 }}>{value}</div>
    </div>
  );
}

// Ranked Stat Card Component - Shows stat with ranking among active managers
function RankedStatCard({ title, value, color, rank, worst, isMobile }) {
  // Determine rank color based on dynamic thirds
  const getRankColor = (r, w) => {
    if (!r || !w) return 'var(--text)';
    const firstThird = Math.ceil(w / 3);
    const secondThird = Math.ceil((2 * w) / 3);

    if (r <= firstThird) return 'var(--success)';
    if (r <= secondThird) return 'var(--muted)';
    return 'var(--danger)';
  };

  const rankColor = getRankColor(rank, worst);
  const textColor = '#000000'; // Use black text for all circles
  const displayColor = color || rankColor;

  return (
    <div style={{
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: isMobile ? '0.15rem' : '0.25rem'
    }}>
      <div style={{ fontSize: isMobile ? '0.6rem' : '0.75rem', color: 'var(--muted)', textTransform: 'uppercase' }}>{title}</div>
      <div style={{ fontSize: isMobile ? '1.1rem' : '1.5rem', fontWeight: 700, color: displayColor, opacity: 0.85 }}>{value}</div>
      {rank && worst && (
        <div style={{
          width: isMobile ? '22px' : '28px',
          height: isMobile ? '22px' : '28px',
          borderRadius: '50%',
          background: rankColor,
          color: textColor,
          fontSize: isMobile ? '0.7rem' : '0.85rem',
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {rank}
        </div>
      )}
    </div>
  );
}

// Player Stat Card Component - Shows player with their key stat
function PlayerStatCard({ title, player, stat, additionalInfo, isMobile }) {
  // ALL HOOKS MUST COME FIRST (Rules of Hooks)
  const textContainerRef = React.useRef(null);
  const [fontSize, setFontSize] = React.useState(isMobile ? '0.65rem' : '0.95rem');

  // Extract values with optional chaining before useEffect
  const playerName = player?.key || player?.name || '';
  const playerId = player?.player_id;
  const firstName = player?.first_name || (playerName ? playerName.split(' ')[0] : '') || '';
  const lastName = player?.last_name || (playerName ? playerName.split(' ').slice(1).join(' ') : '') || '';
  const statValue = stat === 'num_games_started' ? player?.[stat] : (player?.[stat]?.toFixed(3) || player?.[stat] || 0);

  // Dynamically calculate font size based on actual text width measurement
  React.useEffect(() => {
    if (!isMobile || !textContainerRef.current || !firstName) {
      setFontSize(isMobile ? '0.65rem' : '0.95rem');
      return;
    }

    const calculateFontSize = () => {
      const container = textContainerRef.current;
      if (!container) return;

      // Use requestAnimationFrame to ensure layout is complete
      requestAnimationFrame(() => {
        // Get actual available width from the container
        const availableWidthPx = container.offsetWidth;

        if (availableWidthPx === 0) return; // Not rendered yet

        // Create canvas to measure actual text width
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        // Base font size to test with
        const baseFontSizePx = 0.65 * 16; // 0.65rem in px
        context.font = `600 ${baseFontSizePx}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;

        // Measure actual pixel width of BOTH lines at base font size
        const firstNameWidth = context.measureText(firstName).width;
        const lastNameWidth = context.measureText(lastName).width;

        // Use whichever line is actually wider in pixels
        const maxTextWidth = Math.max(firstNameWidth, lastNameWidth);

        // Calculate required font size to fit with 8% safety buffer
        const requiredFontSizePx = (baseFontSizePx * availableWidthPx) / maxTextWidth * 0.92;

        // Use the smaller of base size or required size, with minimum of 5px
        const minFontSizePx = 5;
        const finalFontSizePx = Math.max(minFontSizePx, Math.min(baseFontSizePx, requiredFontSizePx));

        setFontSize(`${finalFontSizePx / 16}rem`);
      });
    };

    // Calculate with a slight delay to ensure DOM is ready
    const timeoutId = setTimeout(calculateFontSize, 10);

    // Recalculate on window resize
    window.addEventListener('resize', calculateFontSize);
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', calculateFontSize);
    };
  }, [isMobile, firstName, lastName]);

  // CONDITIONAL RETURNS COME AFTER ALL HOOKS
  if (!player) {
    return (
      <div style={{
        padding: isMobile ? '0.5rem' : '1rem',
        background: 'var(--bg-alt)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        textAlign: 'center',
        minHeight: isMobile ? '80px' : '120px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: 'var(--muted)', fontSize: isMobile ? '0.7rem' : '0.85rem' }}>Loading...</div>
      </div>
    );
  }

  // Determine stat value color based on title
  const getStatValueColor = () => {
    if (title === "Highest ffWAR") return 'var(--success)';
    if (title === "Lowest ffWAR" && parseFloat(statValue) < 0) return 'var(--danger)';
    return 'var(--text)';
  };

  return (
    <div
      style={{
        padding: isMobile ? '0.25rem' : '0.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: isMobile ? '0.25rem' : '0.5rem',
        minWidth: 0,
        overflow: 'hidden',
        ...(!isMobile && { alignItems: 'flex-start' })
      }}
    >
      <div style={{
        fontSize: isMobile ? '0.7rem' : '1.25rem',
        fontWeight: 700,
        color: 'var(--text)',
        textAlign: 'left',
        letterSpacing: isMobile ? '0.5px' : '1px'
      }}>
        {title}
      </div>

      {isMobile ? (
        // Mobile: Original structure with div wrapper and separate link on name
        <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '0.25rem' : '0.5rem' }}>
          {player.player_image_endpoint && (
            <Link to={`/player/${playerId}`} style={{ flexShrink: 0 }}>
              <img
                src={player.player_image_endpoint}
                alt={playerName}
                style={{
                  width: isMobile ? '50px' : '75px',
                  height: isMobile ? '50px' : '75px',
                  borderRadius: '8px',
                  objectFit: 'cover',
                  cursor: 'pointer'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            </Link>
          )}
          {/* Vertical Divider */}
          {player.player_image_endpoint && <div style={{ width: '1px', height: isMobile ? '50px' : '75px', background: 'var(--border)', flexShrink: 0 }} />}
          <div ref={textContainerRef} style={{ minWidth: 0, textAlign: 'left', width: '100%' }}>
            <Link
              to={`/player/${playerId}`}
              style={{
                fontWeight: 600,
                fontSize: fontSize,
                color: 'var(--text)',
                textDecoration: 'none',
                lineHeight: '1.2',
                display: 'block',
                transition: 'color 0.2s ease',
                overflow: 'hidden',
                whiteSpace: 'nowrap'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = 'var(--accent)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = 'var(--text)';
              }}
            >
              <div style={{ overflow: 'hidden', textOverflow: 'clip' }}>{firstName}</div>
              <div style={{ overflow: 'hidden', textOverflow: 'clip' }}>{lastName}</div>
            </Link>
            <div style={{ fontSize: isMobile ? '0.45rem' : '0.8rem', color: 'var(--muted)', whiteSpace: 'nowrap' }}>
              {player.position} • {player.team}
            </div>
            <div style={{ fontSize: isMobile ? '0.75rem' : '1.1rem', fontWeight: 700, color: getStatValueColor(), marginTop: isMobile ? '0.15rem' : '0.25rem', opacity: 0.85 }}>
              {statValue}
            </div>
            {additionalInfo && (
              <div style={{ fontSize: isMobile ? '0.45rem' : '0.75rem', color: 'var(--muted)', marginTop: isMobile ? '0.15rem' : '0.25rem', whiteSpace: 'nowrap' }}>
                {additionalInfo}
              </div>
            )}
          </div>
        </div>
      ) : (
        // Desktop: New structure with Link wrapper and hover border
        <Link
          to={`/player/${playerId}`}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.25rem',
            border: '1px solid transparent',
            background: 'transparent',
            borderRadius: '8px',
            transition: 'all 0.2s ease',
            cursor: 'pointer',
            textDecoration: 'none'
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
          {player.player_image_endpoint && (
            <img
              src={player.player_image_endpoint}
              alt={playerName}
              style={{
                width: '75px',
                height: '75px',
                borderRadius: '8px',
                objectFit: 'cover',
                flexShrink: 0
              }}
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          )}
          {/* Vertical Divider */}
          {player.player_image_endpoint && <div style={{ width: '1px', height: '75px', background: 'var(--border)', flexShrink: 0 }} />}
          <div ref={textContainerRef} style={{ minWidth: 0, textAlign: 'left' }}>
            <div
              style={{
                fontWeight: 600,
                fontSize: fontSize,
                color: 'var(--text)',
                lineHeight: '1.2',
                display: 'block',
                overflow: 'hidden',
                whiteSpace: 'nowrap'
              }}
            >
              <div style={{ overflow: 'hidden', textOverflow: 'clip' }}>{firstName}</div>
              <div style={{ overflow: 'hidden', textOverflow: 'clip' }}>{lastName}</div>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--muted)', whiteSpace: 'nowrap' }}>
              {player.position} • {player.team}
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: getStatValueColor(), marginTop: '0.25rem', opacity: 0.85 }}>
              {statValue}
            </div>
            {additionalInfo && (
              <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem', whiteSpace: 'nowrap' }}>
                {additionalInfo}
              </div>
            )}
          </div>
        </Link>
      )}
    </div>
  );
}

// PlayerLink Component - Displays player with image and clickable link
function PlayerLink({ player, showImage = true }) {
  const playerName = typeof player === 'string' ? player : player?.name || 'Unknown';
  const playerId = typeof player === 'object' ? player?.player_id : null;
  const imageUrl = typeof player === 'object' ? player?.image_url : null;

  // Check if this is FAAB or a draft pick (not a real player)
  const isFAAB = playerName.toLowerCase().includes('faab');
  const isDraftPick = playerName.toLowerCase().includes('draft pick') ||
                      playerName.toLowerCase().includes('round pick') ||
                      /\d{4}\s+(1st|2nd|3rd|4th|5th|6th|7th)\s+round/i.test(playerName);
  const shouldLink = !isFAAB && !isDraftPick;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      {showImage && imageUrl && (
        <img
          src={imageUrl}
          alt={playerName}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '4px',
            objectFit: 'cover',
            flexShrink: 0
          }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      )}
      {shouldLink ? (
        <Link
          to={`/player/${playerId}`}
          style={{
            color: 'var(--text)',
            textDecoration: 'none',
            fontWeight: 600,
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--accent)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text)';
          }}
        >
          {playerName}
        </Link>
      ) : (
        <span style={{ fontWeight: 600, color: 'var(--text)', opacity: 0.7 }}>
          {playerName}
        </span>
      )}
    </div>
  );
}

// ManagerLink Component - Displays manager with image and clickable link
function ManagerLink({ manager, showImage = true }) {
  const managerName = typeof manager === 'string' ? manager : manager?.name || 'Unknown';
  const imageUrl = typeof manager === 'object' ? manager?.image_url : null;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      {showImage && imageUrl && (
        <img
          src={imageUrl}
          alt={managerName}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            objectFit: 'cover',
            border: '2px solid var(--border)',
            flexShrink: 0
          }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      )}
      <Link
        to={`/manager/${encodeURIComponent(managerName)}`}
        style={{
          color: 'var(--text)',
          textDecoration: 'none',
          fontWeight: 600,
          transition: 'color 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = 'var(--accent)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = 'var(--text)';
        }}
      >
        {managerName}
      </Link>
    </div>
  );
}

// Helper function to format records (hide ties if 0)
function formatRecord(wins, losses, ties) {
  return ties === 0 ? `${wins}-${losses}` : `${wins}-${losses}-${ties}`;
}

// Helper function to format years active as a compact range
function formatYearsActive(years) {
  if (!years || years.length === 0) return 'N/A';
  if (years.length === 1) return `${years[0]} (1 season)`;

  const sortedYears = [...years].map(y => Number(y)).sort((a, b) => a - b);
  const first = sortedYears[0];
  const last = sortedYears[sortedYears.length - 1];
  const count = sortedYears.length;

  // Check if years are continuous (no gaps)
  const isContinuous = sortedYears.every((year, i) => {
    if (i === 0) return true;
    return year === sortedYears[i - 1] + 1;
  });

  // Show individual years only if there are gaps AND 4 or fewer years
  const yearsText = (!isContinuous && count <= 4)
    ? sortedYears.join(', ')
    : `${first} - ${last}`;

  return (
    <>
      {yearsText}
      <br />
      <span style={{ fontSize: '0.85rem' }}>({count} season{count !== 1 ? 's' : ''})</span>
    </>
  );
}

// Overview Tab
function OverviewTab({ overall, regularSeason, playoffs, trades, adds, drops, faab, placements, headToHead, managerName, awardsData, isMobile }) {
  const [hoveredMatchupId, setHoveredMatchupId] = useState(null);
  const hideTimeoutRef = useRef(null);
  const navigate = useNavigate();

  // Sort opponents by wins first, then win percentage as tie breaker
  const sortedOpponents = headToHead ? Object.entries(headToHead).sort((a, b) => {
    // First sort by wins (descending)
    if (b[1].wins !== a[1].wins) {
      return b[1].wins - a[1].wins;
    }
    // If wins are equal, sort by win percentage
    const totalA = a[1].wins + a[1].losses + a[1].ties;
    const totalB = b[1].wins + b[1].losses + b[1].ties;
    const winPctA = totalA > 0 ? (a[1].wins / totalA) : 0;
    const winPctB = totalB > 0 ? (b[1].wins / totalB) : 0;
    return winPctB - winPctA;
  }) : [];

  return (
    <div style={{
      display: 'flex',
      flexDirection: isMobile ? 'column' : 'row',
      gap: isMobile ? '1.5rem' : '2rem',
      width: '100%',
      maxWidth: '100%',
      overflow: 'hidden'
    }}>
      {/* Left Side - 2 Column Flowing Grid */}
      <div style={{
        flex: 1,
        display: 'grid',
        gridTemplateColumns: isMobile ? '1fr' : 'repeat(2, minmax(200px, 1fr))',
        gap: isMobile ? '1rem' : '0.5rem 3rem',
        alignContent: 'start',
        minWidth: isMobile ? '0' : '680px',
        maxWidth: isMobile ? '100%' : '680px',
        width: isMobile ? '100%' : 'auto'
      }}>
        {/* Head-to-Head Dropdown (Mobile Only) */}
        {isMobile && sortedOpponents.length > 0 && (
          <div style={{
            gridColumn: '1 / -1',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem',
            alignItems: 'center',
            marginBottom: '0.5rem'
          }}>
            <div style={{
              fontSize: '0.9rem',
              fontWeight: 600,
              color: 'var(--text)',
              textAlign: 'center'
            }}>
              See Head-to-Head Details
            </div>
            <select
              onChange={(e) => {
                const selectedIndex = parseInt(e.target.value, 10);
                if (selectedIndex >= 0 && sortedOpponents[selectedIndex]) {
                  const [opponentKey, data] = sortedOpponents[selectedIndex];
                  const opponent = data.opponent || { name: opponentKey };
                  navigate(`/head-to-head?manager1=${encodeURIComponent(managerName)}&manager2=${encodeURIComponent(opponent.name)}`);
                }
              }}
              defaultValue=""
              style={{
                padding: '0.5rem 1rem',
                fontSize: '0.85rem',
                color: 'var(--text)',
                background: 'var(--bg-alt)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                cursor: 'pointer',
                outline: 'none',
                minWidth: '200px',
                maxWidth: '90%',
                textAlign: 'center'
              }}
            >
              <option value="" disabled>Select an opponent</option>
              {sortedOpponents.map(([opponentKey, data], index) => {
                const opponent = data.opponent || { name: opponentKey };
                const record = formatRecord(data.wins, data.losses, data.ties);
                return (
                  <option key={opponentKey} value={index}>
                    {opponent.name} ({record})
                  </option>
                );
              })}
            </select>
          </div>
        )}

        {/* Season Stats */}
        <Section title="Season Stats">
          <StatRow label="Regular Season" value={formatRecord(regularSeason.wins || 0, regularSeason.losses || 0, regularSeason.ties || 0)} />
          <StatRow label="Playoffs" value={formatRecord(playoffs.wins || 0, playoffs.losses || 0, playoffs.ties || 0)} />
          <StatRow label="AVG PF" value={overall.average_points_for?.toFixed(2) || 0} />
          <StatRow label="AVG PA" value={overall.average_points_against?.toFixed(2) || 0} />
        </Section>

        {/* Matchup Stats */}
        {awardsData && (
          <Section title={
            <>
              Matchup Stats{' '}
              {!isMobile && (
                <span style={{ fontSize: '0.75rem', fontWeight: 400, opacity: 0.6, letterSpacing: '0px' }}>
                  (hover for details)
                </span>
              )}
            </>
          }>
            {awardsData.highest_weekly_score && awardsData.highest_weekly_score.manager_1_score > 0 && (
              <HoverableMatchupStat
                id="highest"
                label="Highest Score"
                displayText={`${awardsData.highest_weekly_score.manager_1_score.toFixed(2)} v ${awardsData.highest_weekly_score.manager_2.name} [${awardsData.highest_weekly_score.year} W${awardsData.highest_weekly_score.week}]`}
                matchup={awardsData.highest_weekly_score}
                hoveredMatchupId={hoveredMatchupId}
                setHoveredMatchupId={setHoveredMatchupId}
                hideTimeoutRef={hideTimeoutRef}
                isMobile={isMobile}
                managerName={managerName}
              />
            )}
            {awardsData.lowest_weekly_score && awardsData.lowest_weekly_score.manager_1_score < Infinity && (
              <HoverableMatchupStat
                id="lowest"
                label="Lowest Score"
                displayText={`${awardsData.lowest_weekly_score.manager_1_score.toFixed(2)} v ${awardsData.lowest_weekly_score.manager_2.name} [${awardsData.lowest_weekly_score.year} W${awardsData.lowest_weekly_score.week}]`}
                matchup={awardsData.lowest_weekly_score}
                hoveredMatchupId={hoveredMatchupId}
                setHoveredMatchupId={setHoveredMatchupId}
                hideTimeoutRef={hideTimeoutRef}
                isMobile={isMobile}
                managerName={managerName}
              />
            )}
            {awardsData.biggest_blowout_win && awardsData.biggest_blowout_win.differential > 0 && (
              <HoverableMatchupStat
                id="blowout-win"
                label="Best Blowout"
                displayText={`+${awardsData.biggest_blowout_win.differential.toFixed(2)} v ${awardsData.biggest_blowout_win.manager_2.name} [${awardsData.biggest_blowout_win.year} W${awardsData.biggest_blowout_win.week}]`}
                matchup={awardsData.biggest_blowout_win}
                showMargin={true}
                hoveredMatchupId={hoveredMatchupId}
                setHoveredMatchupId={setHoveredMatchupId}
                hideTimeoutRef={hideTimeoutRef}
                isMobile={isMobile}
                managerName={managerName}
              />
            )}
            {awardsData.biggest_blowout_loss && awardsData.biggest_blowout_loss.differential < 0 && (
              <HoverableMatchupStat
                id="blowout-loss"
                label="Worst Blowout"
                displayText={`${awardsData.biggest_blowout_loss.differential.toFixed(2)} v ${awardsData.biggest_blowout_loss.manager_2.name} [${awardsData.biggest_blowout_loss.year} W${awardsData.biggest_blowout_loss.week}]`}
                matchup={awardsData.biggest_blowout_loss}
                showMargin={true}
                hoveredMatchupId={hoveredMatchupId}
                setHoveredMatchupId={setHoveredMatchupId}
                hideTimeoutRef={hideTimeoutRef}
                isMobile={isMobile}
                managerName={managerName}
              />
            )}
          </Section>
        )}

        {/* Transaction Summary */}
        <Section title="Transactions">
          <StatRow label="Trades" value={trades.total || 0} />
          <StatRow label="Adds" value={adds.total || 0} />
          <StatRow label="Drops" value={drops.total || 0} />
          <StatRow label="FAAB Spent" value={`$${faab.total_spent || 0}`} />
        </Section>

        {/* Placement History */}
        <Section title={
          <>
            Placements{' '}
            {!isMobile && placements.length > 0 && (
              <span style={{ fontSize: '0.75rem', fontWeight: 400, opacity: 0.6, letterSpacing: '0px' }}>
                (hover for details)
              </span>
            )}
          </>
        }>
          {placements.length > 0 ? (
            <div>
              {placements.sort((a, b) => b.year - a.year).map((p, i) => (
                <HoverablePlacement
                  key={p.year}
                  placement={p}
                  hoveredMatchupId={hoveredMatchupId}
                  setHoveredMatchupId={setHoveredMatchupId}
                  hideTimeoutRef={hideTimeoutRef}
                  isMobile={isMobile}
                  managerName={managerName}
                  isLast={i === placements.length - 1}
                />
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '0.9rem', color: 'var(--muted)', fontStyle: 'italic' }}>
              Manager has never won 1st, 2nd, or 3rd.
            </div>
          )}
        </Section>

        {/* Top Trade Partners */}
        {trades.top_trade_partners && trades.top_trade_partners.length > 0 && (
          <Section title="Top Trade Partners">
            {trades.top_trade_partners.slice(0, 5).map((partner, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <ManagerLink manager={partner} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>{partner.count} trades</span>
              </div>
            ))}
          </Section>
        )}

        {/* Top Players Added */}
        {adds.top_players_added && adds.top_players_added.length > 0 && (
          <Section title="Most Added Players">
            {adds.top_players_added.slice(0, 5).map((player, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <PlayerLink player={player} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
              </div>
            ))}
          </Section>
        )}

        {/* Top Players Dropped */}
        {drops.top_players_dropped && drops.top_players_dropped.length > 0 && (
          <Section title="Most Dropped Players">
            {drops.top_players_dropped.slice(0, 5).map((player, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <PlayerLink player={player} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
              </div>
            ))}
          </Section>
        )}

        {/* Most Acquired via Trade */}
        {trades.most_aquired_players && trades.most_aquired_players.length > 0 && (
          <Section title="Most Acquired (Trade)">
            {trades.most_aquired_players.slice(0, 3).map((player, i) => (
              <div key={i} style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                  <PlayerLink player={player} />
                  <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
                </div>
                {player.from && player.from.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem', paddingLeft: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                    <span>From:</span>
                    {player.from.map((m, j) => (
                      <span key={j} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <ManagerLink manager={m} showImage={false} />
                        <span>({m.count})</span>
                        {j < player.from.length - 1 && <span>,</span>}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </Section>
        )}

        {/* Most Sent via Trade */}
        {trades.most_sent_players && trades.most_sent_players.length > 0 && (
          <Section title="Most Sent (Trade)">
            {trades.most_sent_players.slice(0, 3).map((player, i) => (
              <div key={i} style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                  <PlayerLink player={player} />
                  <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
                </div>
                {player.to && player.to.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem', paddingLeft: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                    <span>To:</span>
                    {player.to.map((m, j) => (
                      <span key={j} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <ManagerLink manager={m} showImage={false} />
                        <span>({m.count})</span>
                        {j < player.to.length - 1 && <span>,</span>}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </Section>
        )}

        {/* FAAB Biggest Acquisitions */}
        {faab.biggest_acquisitions && faab.biggest_acquisitions.length > 0 && (
          <Section title="Biggest FAAB Bids">
            {faab.biggest_acquisitions.map((bid, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <PlayerLink player={bid} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>${bid.amount}</span>
              </div>
            ))}
          </Section>
        )}

        {/* FAAB Traded */}
        {faab.faab_traded && (
          <Section title="FAAB Trading">
            <StatRow label="Sent" value={`$${faab.faab_traded.sent || 0}`} color="var(--danger)" />
            <StatRow label="Received" value={`$${faab.faab_traded.received || 0}`} color="var(--success)" />
            <StatRow label="Net" value={`$${faab.faab_traded.net || 0}`} color={faab.faab_traded.net > 0 ? 'var(--success)' : faab.faab_traded.net < 0 ? 'var(--danger)' : undefined} />
          </Section>
        )}
      </div>

      {/* Right Sidebar - Head-to-Head (Desktop Only) */}
      {!isMobile && sortedOpponents.length > 0 && (
        <div style={{ width: '280px', flexShrink: 0 }}>
            <h3 style={{ marginBottom: isMobile ? '0.75rem' : '1rem', fontSize: isMobile ? '1.1rem' : '1.25rem', fontWeight: 700, letterSpacing: '1px' }}>Head-to-Head</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: isMobile ? '0.5rem' : '0.75rem' }}>
              {sortedOpponents.map(([opponentKey, data]) => {
              const opponent = data.opponent || { name: opponentKey };
              const totalGames = data.wins + data.losses + data.ties;
              const winPct = totalGames > 0 ? ((data.wins / totalGames) * 100).toFixed(1) : '0.0';
              const tradesCount = data.num_trades_between || 0;
              const pointsFor = data.points_for || 0;
              const pointsAgainst = data.points_against || 0;
              const avgPointsFor = totalGames > 0 ? (pointsFor / totalGames).toFixed(1) : '0.0';
              const avgPointsAgainst = totalGames > 0 ? (pointsAgainst / totalGames).toFixed(1) : '0.0';

              return (
                <Link
                  key={opponentKey}
                  to={`/head-to-head?manager1=${encodeURIComponent(managerName)}&manager2=${encodeURIComponent(opponent.name)}`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                    padding: '0.75rem',
                    background: 'var(--bg-alt)',
                    borderRadius: '8px',
                    border: '1px solid var(--border)',
                    transition: 'all 0.2s ease',
                    textDecoration: 'none',
                    cursor: 'pointer'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'var(--bg)';
                    e.currentTarget.style.borderColor = 'var(--accent)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'var(--bg-alt)';
                    e.currentTarget.style.borderColor = 'var(--border)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ flexShrink: 0, display: 'flex', justifyContent: 'center' }}>
                      {opponent.image_url && (
                        <img
                          src={opponent.image_url}
                          alt={opponent.name}
                          style={{
                            width: '64px',
                            height: '64px',
                            borderRadius: '50%',
                            objectFit: 'cover',
                            border: '2px solid var(--border)'
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div
                        style={{
                          fontWeight: 600,
                          fontSize: '1rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          color: 'var(--text)'
                        }}
                      >
                        {opponent.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                        <span>{formatRecord(data.wins, data.losses, data.ties)}</span>
                        {' • '}
                        <span style={{
                          fontWeight: 600,
                          color: parseFloat(winPct) >= 50 ? 'var(--success)' : 'var(--danger)',
                          opacity: 0.85
                        }}>
                          {winPct}%
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
                        <div>Avg: {avgPointsFor} - {avgPointsAgainst}</div>
                        {tradesCount > 0 && (
                          <div>{tradesCount} trade{tradesCount !== 1 ? 's' : ''}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Head-to-Head Matchup Details Page Component

// Awards Tab - Compact grid layout
function AwardsTab({ awardsData, MatchupCard }) {
  return (
    <div>
      {/* Matchup Awards in 2-column grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Highest Weekly Score */}
        {awardsData.highest_weekly_score && awardsData.highest_weekly_score.manager_1_score > 0 && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--success)' }}>🎯 Highest Weekly Score</h3>
            <MatchupCard matchup={awardsData.highest_weekly_score} />
          </div>
        )}

        {/* Lowest Weekly Score */}
        {awardsData.lowest_weekly_score && awardsData.lowest_weekly_score.manager_1_score < Infinity && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--danger)' }}>📉 Lowest Weekly Score</h3>
            <MatchupCard matchup={awardsData.lowest_weekly_score} />
          </div>
        )}

        {/* Biggest Blowout Win */}
        {awardsData.biggest_blowout_win && awardsData.biggest_blowout_win.differential > 0 && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--success)' }}>💥 Biggest Blowout Win</h3>
            <MatchupCard matchup={awardsData.biggest_blowout_win} showMargin={true} />
          </div>
        )}

        {/* Biggest Blowout Loss */}
        {awardsData.biggest_blowout_loss && awardsData.biggest_blowout_loss.differential < 0 && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--danger)' }}>😭 Biggest Blowout Loss</h3>
            <MatchupCard matchup={awardsData.biggest_blowout_loss} showMargin={true} />
          </div>
        )}
      </div>

      {/* Activity Awards in horizontal cards */}
      {(awardsData.biggest_faab_bid?.amount > 0 || awardsData.most_trades_in_year?.count > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {/* Biggest FAAB Bid */}
          {awardsData.biggest_faab_bid && awardsData.biggest_faab_bid.amount > 0 && (
            <div style={{
              padding: '1.5rem',
              background: 'var(--bg-alt)',
              borderRadius: '12px',
              border: '1px solid var(--border)'
            }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', fontWeight: 600 }}>
                💰 Biggest FAAB Bid
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.5rem', opacity: 0.85 }}>
                ${awardsData.biggest_faab_bid.amount}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                {awardsData.biggest_faab_bid.player?.name || awardsData.biggest_faab_bid.player} ({awardsData.biggest_faab_bid.year})
              </div>
            </div>
          )}

          {/* Most Trades in Year */}
          {awardsData.most_trades_in_year && awardsData.most_trades_in_year.count > 0 && (
            <div style={{
              padding: '1.5rem',
              background: 'var(--bg-alt)',
              borderRadius: '12px',
              border: '1px solid var(--border)'
            }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', fontWeight: 600 }}>
                🔄 Most Trades (Single Season)
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.5rem', opacity: 0.85 }}>
                {awardsData.most_trades_in_year.count}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                {awardsData.most_trades_in_year.year}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Section Component
function Section({ title, children, style }) {
  return (
    <div style={{ ...style }}>
      <h3 style={{ marginBottom: '0.75rem', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '1px' }}>{title}</h3>
      {children}
    </div>
  );
}

// StatRow Component
function StatRow({ label, value, color, small }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.25rem 0',
      fontSize: small ? '0.85rem' : '0.95rem'
    }}>
      <span style={{ color: 'var(--muted)' }}>{label}</span>
      <span style={{ fontWeight: 600, color: color || 'var(--text)', opacity: 0.85 }}>{value}</span>
    </div>
  );
}

// HoverableMatchupStat Component - Shows MatchupCard on hover (desktop) or navigates to matchup page (mobile)
function HoverablePlacement({ placement, hoveredMatchupId, setHoveredMatchupId, hideTimeoutRef, isMobile = false, managerName, isLast = false }) {
  const [cardPosition, setCardPosition] = useState({ top: 0, left: 0 });
  const textRef = useRef(null);
  const cardRef = useRef(null);

  const id = `placement-${placement.year}`;
  const isHovered = hoveredMatchupId === id;
  const matchup = placement.matchup_card;
  const hasMatchupCard = matchup && Object.keys(matchup).length > 0;

  // Get placement display text
  const getPlacementText = (place) => {
    if (place === 1) return '🥇 Champion';
    if (place === 2) return '🥈 Runner-up';
    if (place === 3) return '🥉 3rd Place';
    return `${place}th`;
  };

  useEffect(() => {
    if (isHovered && textRef.current && cardRef.current) {
      const textRect = textRef.current.getBoundingClientRect();
      const cardRect = cardRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      const spacing = 16;

      const spaceRight = viewportWidth - textRect.right;
      const spaceLeft = textRect.left;
      const spaceBelow = viewportHeight - textRect.bottom;

      let top = 0;
      let left = 0;

      if (spaceRight >= cardRect.width + spacing) {
        left = textRect.right + spacing;
        top = textRect.top + (textRect.height / 2) - (cardRect.height / 2);
      } else if (spaceLeft >= cardRect.width + spacing) {
        left = textRect.left - cardRect.width - spacing;
        top = textRect.top + (textRect.height / 2) - (cardRect.height / 2);
      } else if (spaceBelow >= cardRect.height + spacing) {
        top = textRect.bottom + spacing;
        left = textRect.left + (textRect.width / 2) - (cardRect.width / 2);
      } else {
        top = textRect.top - cardRect.height - spacing;
        left = textRect.left + (textRect.width / 2) - (cardRect.width / 2);
      }

      top = Math.max(spacing, Math.min(top, viewportHeight - cardRect.height - spacing));
      left = Math.max(spacing, Math.min(left, viewportWidth - cardRect.width - spacing));

      setCardPosition({ top, left });
    }
  }, [isHovered]);

  // Construct matchup URL for mobile
  const matchupUrl = hasMatchupCard ? `/matchup?year=${matchup.year}&week=${matchup.week}&manager1=${encodeURIComponent(managerName)}&manager2=${encodeURIComponent(matchup.manager_2?.name || '')}` : '#';

  const rowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.25rem 0',
    borderBottom: isLast ? 'none' : '1px solid var(--border)'
  };

  // No matchup card available - render plain text
  if (!hasMatchupCard) {
    return (
      <div style={rowStyle}>
        <span>{placement.year}</span>
        <span style={{ fontWeight: 700, opacity: 0.85 }}>
          {getPlacementText(placement.placement)}
        </span>
      </div>
    );
  }

  // Mobile version: clickable link
  if (isMobile) {
    return (
      <Link
        to={matchupUrl}
        state={{ matchup }}
        style={{
          ...rowStyle,
          textDecoration: 'none'
        }}
      >
        <span style={{ color: 'var(--text)' }}>{placement.year}</span>
        <span
          style={{
            fontWeight: 700,
            color: 'var(--accent)',
            opacity: 0.9
          }}
        >
          {getPlacementText(placement.placement)} →
        </span>
      </Link>
    );
  }

  // Desktop version: hover behavior
  return (
    <div style={{ ...rowStyle, position: 'relative' }}>
      <span>{placement.year}</span>
      <span
        ref={textRef}
        style={{
          fontWeight: 700,
          opacity: 0.85,
          cursor: 'pointer',
          borderBottom: isHovered ? '1px solid var(--text)' : '1px dotted rgba(255, 255, 255, 0.4)',
          transition: 'border-bottom 0.2s ease'
        }}
        onMouseEnter={() => {
          if (hideTimeoutRef.current) {
            clearTimeout(hideTimeoutRef.current);
          }
          setHoveredMatchupId(id);
        }}
        onMouseLeave={() => {
          hideTimeoutRef.current = setTimeout(() => {
            setHoveredMatchupId(null);
          }, 300);
        }}
      >
        {getPlacementText(placement.placement)}
      </span>

      {/* Hovering MatchupCard */}
      {isHovered && (
        <div
          ref={cardRef}
          onMouseEnter={() => {
            if (hideTimeoutRef.current) {
              clearTimeout(hideTimeoutRef.current);
            }
            setHoveredMatchupId(id);
          }}
          onMouseLeave={() => {
            setHoveredMatchupId(null);
          }}
          style={{
            position: 'fixed',
            top: `${cardPosition.top}px`,
            left: `${cardPosition.left}px`,
            zIndex: 9999,
            pointerEvents: 'auto',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
            borderRadius: '12px',
            backgroundColor: 'rgba(20, 20, 30, 0.92)',
            border: '2px solid var(--accent)',
            transition: 'opacity 0.2s ease',
            opacity: cardPosition.top === 0 ? 0 : 1,
          }}>
          <MatchupCard matchup={matchup} />
        </div>
      )}
    </div>
  );
}

function HoverableMatchupStat({ id, label, displayText, matchup, showMargin = false, hoveredMatchupId, setHoveredMatchupId, hideTimeoutRef, isMobile = false, managerName }) {
  const [cardPosition, setCardPosition] = useState({ top: 0, left: 0 });
  const textRef = useRef(null);
  const cardRef = useRef(null);

  const isHovered = hoveredMatchupId === id;

  useEffect(() => {
    if (isHovered && textRef.current && cardRef.current) {
      const textRect = textRef.current.getBoundingClientRect();
      const cardRect = cardRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      const spacing = 16; // Space between text and card

      // Calculate available space in each direction
      const spaceRight = viewportWidth - textRect.right;
      const spaceLeft = textRect.left;
      const spaceBelow = viewportHeight - textRect.bottom;
      const spaceAbove = textRect.top;

      let top = 0;
      let left = 0;

      // Determine horizontal position (prefer right, then left)
      if (spaceRight >= cardRect.width + spacing) {
        // Position to the right
        left = textRect.right + spacing;
        top = textRect.top + (textRect.height / 2) - (cardRect.height / 2);
      } else if (spaceLeft >= cardRect.width + spacing) {
        // Position to the left
        left = textRect.left - cardRect.width - spacing;
        top = textRect.top + (textRect.height / 2) - (cardRect.height / 2);
      } else if (spaceBelow >= cardRect.height + spacing) {
        // Position below
        top = textRect.bottom + spacing;
        left = textRect.left + (textRect.width / 2) - (cardRect.width / 2);
      } else {
        // Position above
        top = textRect.top - cardRect.height - spacing;
        left = textRect.left + (textRect.width / 2) - (cardRect.width / 2);
      }

      // Ensure card stays within viewport bounds
      top = Math.max(spacing, Math.min(top, viewportHeight - cardRect.height - spacing));
      left = Math.max(spacing, Math.min(left, viewportWidth - cardRect.width - spacing));

      setCardPosition({ top, left });
    }
  }, [isHovered]);

  // Construct matchup URL for mobile
  const matchupUrl = matchup ? `/matchup?year=${matchup.year}&week=${matchup.week}&manager1=${encodeURIComponent(managerName)}&manager2=${encodeURIComponent(matchup.manager_2.name)}` : '#';

  // Mobile version: clickable link
  if (isMobile) {
    return (
      <Link
        to={matchupUrl}
        state={{ matchup, showMargin }}
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0.25rem 0',
          fontSize: '0.95rem',
          textDecoration: 'none'
        }}
      >
        <span style={{ color: 'var(--muted)' }}>{label}</span>
        <span
          style={{
            fontWeight: 600,
            color: 'var(--accent)',
            opacity: 0.9,
            fontSize: '0.85rem'
          }}
        >
          {displayText} →
        </span>
      </Link>
    );
  }

  // Desktop version: hover behavior
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.25rem 0',
      fontSize: '0.95rem',
      position: 'relative'
    }}>
      <span style={{ color: 'var(--muted)' }}>{label}</span>
      <span
        ref={textRef}
        style={{
          fontWeight: 600,
          color: 'var(--text)',
          opacity: 0.85,
          fontSize: '0.85rem',
          cursor: 'pointer',
          borderBottom: isHovered ? '1px solid var(--text)' : '1px dotted rgba(255, 255, 255, 0.4)',
          transition: 'border-bottom 0.2s ease'
        }}
        onMouseEnter={() => {
          if (hideTimeoutRef.current) {
            clearTimeout(hideTimeoutRef.current);
          }
          setHoveredMatchupId(id);
        }}
        onMouseLeave={() => {
          hideTimeoutRef.current = setTimeout(() => {
            setHoveredMatchupId(null);
          }, 300);
        }}
      >
        {displayText}
      </span>

      {/* Hovering MatchupCard */}
      {isHovered && matchup && (
        <div
          ref={cardRef}
          onMouseEnter={() => {
            if (hideTimeoutRef.current) {
              clearTimeout(hideTimeoutRef.current);
            }
            setHoveredMatchupId(id);
          }}
          onMouseLeave={() => {
            setHoveredMatchupId(null);
          }}
          style={{
            position: 'fixed',
            top: `${cardPosition.top}px`,
            left: `${cardPosition.left}px`,
            zIndex: 9999,
            pointerEvents: 'auto',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
            borderRadius: '12px',
            backgroundColor: 'rgba(20, 20, 30, 0.92)',
            border: '2px solid var(--accent)',
            transition: 'opacity 0.2s ease',
            opacity: cardPosition.top === 0 ? 0 : 1,
          }}>
          <MatchupCard matchup={matchup} showMargin={showMargin} />
        </div>
      )}
    </div>
  );
}
