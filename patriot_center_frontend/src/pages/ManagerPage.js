import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useManagerSummary } from '../hooks/useManagerSummary';
import { useManagerAwards } from '../hooks/useManagerAwards';
import { useManagerTransactions } from '../hooks/useManagerTransactions';
import { useManagerYearlyData } from '../hooks/useManagerYearlyData';
import { useHeadToHead } from '../hooks/useHeadToHead';

/**
 * ManagerPage - Social media style profile view with ALL manager data
 */
export default function ManagerPage() {
  const { managerName } = useParams();
  const navigate = useNavigate();

  const [year, setYear] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [transactionPage, setTransactionPage] = useState(0);
  const [typeFilter, setTypeFilter] = useState('all');
  const transactionsPerPage = 20;

  // Fetch data from ALL endpoints
  const { summary, loading: summaryLoading, error: summaryError } = useManagerSummary(managerName, { year });
  const { awards, loading: awardsLoading } = useManagerAwards(managerName);
  const { transactions: transactionHistory, loading: transactionsLoading } = useManagerTransactions(
    managerName,
    { year, type: typeFilter === 'all' ? undefined : typeFilter, limit: transactionsPerPage, offset: transactionPage * transactionsPerPage }
  );
  const { yearlyData, loading: yearlyLoading } = useManagerYearlyData(managerName, year);

  React.useEffect(() => {
    setImageError(false);
  }, [managerName]);

  const loading = summaryLoading || awardsLoading || transactionsLoading || (year && yearlyLoading);
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
  const championships = overallData.championships || 0;
  const awardsData = awards?.awards || {};

  // Calculate medal counts
  const medalCounts = placements.reduce((acc, p) => {
    if (p.placement === 1) acc.gold++;
    else if (p.placement === 2) acc.silver++;
    else if (p.placement === 3) acc.bronze++;
    return acc;
  }, { gold: 0, silver: 0, bronze: 0 });

  // SportsCenter-Style Matchup Card Component
  // Accepts matchup object with manager_1, manager_2, scores, and top_3_scorers
  const MatchupCard = ({ matchup, showMargin = false }) => {
    if (!matchup) return null;

    const manager1 = matchup.manager_1 || {};
    const manager2 = matchup.manager_2 || {};
    const manager1Score = matchup.manager_1_score;
    const manager2Score = matchup.manager_2_score;
    const winner = matchup.winner;
    const week = matchup.week;
    const year = matchup.year;
    const manager1TopScorers = matchup.manager_1_top_3_scorers || [];
    const manager2TopScorers = matchup.manager_2_top_3_scorers || [];

    // Determine result from perspective of manager_1
    let result = 'tie';
    if (winner === manager1.name) result = 'win';
    else if (winner === manager2.name) result = 'loss';

    return (
      <div style={{
        background: 'linear-gradient(135deg, var(--bg-alt) 0%, var(--bg) 100%)',
        borderRadius: '12px',
        border: '2px solid var(--border)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          background: 'var(--bg-alt)',
          padding: '0.5rem 1rem',
          textAlign: 'center',
          color: 'var(--text)',
          fontWeight: 700,
          fontSize: '0.85rem',
          letterSpacing: '0.5px',
          borderBottom: '2px solid var(--border)'
        }}>
          {week && year ? `Week ${week} ${year}` : 'Matchup'}
        </div>

        {/* Score Display with Manager Avatars */}
        <div style={{ padding: '1.5rem' }}>
          {/* Manager Avatars + Score Box */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            {/* Manager 1 Avatar */}
            <Link to={`/manager/${encodeURIComponent(manager1.name)}`} style={{ flexShrink: 0 }}>
              {manager1.image_url && (
                <img
                  src={manager1.image_url}
                  alt={manager1.name}
                  style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '3px solid var(--border)'
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
            </Link>

            {/* Score Box - 2 rows x 2 columns */}
            <div style={{
              flex: 1,
              background: 'var(--bg-alt)',
              border: '2px solid var(--border)',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              {/* Manager 1 Row */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1rem',
                borderBottom: '1px solid var(--border)'
              }}>
                <Link
                  to={`/manager/${encodeURIComponent(manager1.name)}`}
                  style={{
                    flex: 1,
                    fontWeight: 600,
                    fontSize: '1rem',
                    color: result === 'win' ? 'var(--success)' : 'var(--text)',
                    textDecoration: 'none'
                  }}
                >
                  {manager1.name}
                </Link>
                <div style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: result === 'win' ? 'var(--success)' : 'var(--text)',
                  minWidth: '80px',
                  textAlign: 'right'
                }}>
                  {manager1Score?.toFixed(2)}
                </div>
              </div>

              {/* Manager 2 Row */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1rem'
              }}>
                <Link
                  to={`/manager/${encodeURIComponent(manager2.name)}`}
                  style={{
                    flex: 1,
                    fontWeight: 600,
                    fontSize: '1rem',
                    color: result === 'loss' ? 'var(--success)' : 'var(--text)',
                    textDecoration: 'none'
                  }}
                >
                  {manager2.name}
                </Link>
                <div style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: result === 'loss' ? 'var(--success)' : 'var(--text)',
                  minWidth: '80px',
                  textAlign: 'right'
                }}>
                  {manager2Score?.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Manager 2 Avatar */}
            <Link to={`/manager/${encodeURIComponent(manager2.name)}`} style={{ flexShrink: 0 }}>
              {manager2.image_url && (
                <img
                  src={manager2.image_url}
                  alt={manager2.name}
                  style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '3px solid var(--border)'
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
            </Link>
          </div>

          {/* Top 3 Scorers Side by Side */}
          {(manager1TopScorers?.length > 0 || manager2TopScorers?.length > 0) && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              {/* Manager 1 Top Scorers */}
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                  {manager1.name} Top 3
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {manager1TopScorers?.slice(0, 3).map((player, i) => (
                    <div key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem',
                      background: 'var(--bg)',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      fontSize: '0.8rem'
                    }}>
                      {player.image_url && (
                        <img
                          src={player.image_url}
                          alt={player.name}
                          style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '4px',
                            objectFit: 'cover',
                            flexShrink: 0
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Link
                          to={`/player/${encodeURIComponent(player.name)}`}
                          style={{
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            display: 'block',
                            color: 'var(--accent)',
                            textDecoration: 'none'
                          }}
                        >
                          {player.name}
                        </Link>
                        <div style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>
                          {player.position} • {player.score?.toFixed(2)} pts
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Manager 2 Top Scorers */}
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                  {manager2.name} Top 3
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {manager2TopScorers?.slice(0, 3).map((player, i) => (
                    <div key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem',
                      background: 'var(--bg)',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      fontSize: '0.8rem'
                    }}>
                      {player.image_url && (
                        <img
                          src={player.image_url}
                          alt={player.name}
                          style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '4px',
                            objectFit: 'cover',
                            flexShrink: 0
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Link
                          to={`/player/${encodeURIComponent(player.name)}`}
                          style={{
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            display: 'block',
                            color: 'var(--accent)',
                            textDecoration: 'none'
                          }}
                        >
                          {player.name}
                        </Link>
                        <div style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>
                          {player.position} • {player.score?.toFixed(2)} pts
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Margin - Only show for blowouts */}
          {showMargin && matchup.differential !== undefined && (
            <div style={{
              textAlign: 'center',
              fontSize: '0.85rem',
              color: 'var(--muted)',
              paddingTop: '0.75rem',
              marginTop: '0.75rem',
              borderTop: '1px solid var(--border)'
            }}>
              Margin: {Math.abs(matchup.differential).toFixed(2)}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Pagination controls
  const totalPages = transactionHistory ? Math.ceil(transactionHistory.total_count / transactionsPerPage) : 0;

  return (
    <div className="App" style={{ paddingTop: 0, maxWidth: '1400px', margin: '0 auto' }}>
      {/* Back Button */}
      <div style={{ padding: '1rem 2rem' }}>
        <button onClick={() => navigate(-1)} style={{
          background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '1rem', padding: '0.5rem 0'
        }}>← Back to Managers</button>
      </div>

      {/* Hero Banner Section */}
      <div style={{
        background: 'linear-gradient(135deg, var(--accent) 0%, var(--bg-alt) 100%)',
        height: '200px',
        position: 'relative',
        borderRadius: '0 0 16px 16px',
        marginBottom: '80px'
      }}>
        {/* Profile Picture Overlay - Centered */}
        <div style={{
          position: 'absolute',
          bottom: '-60px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '140px',
          height: '140px',
          borderRadius: '50%',
          border: '5px solid var(--bg)',
          background: 'var(--bg-alt)',
          overflow: 'hidden'
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

        {/* Year Filter - Top Right */}
        <div style={{ position: 'absolute', top: '1rem', right: '2rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <label htmlFor="year-select" style={{ color: 'white', fontSize: '0.9rem' }}>Filter:</label>
          <select
            id="year-select"
            value={year || 'ALL'}
            onChange={(e) => setYear(e.target.value === 'ALL' ? null : e.target.value)}
            style={{
              background: 'rgba(255,255,255,0.2)',
              color: 'white',
              border: '1px solid rgba(255,255,255,0.3)',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              cursor: 'pointer',
              backdropFilter: 'blur(10px)'
            }}
          >
            <option value="ALL" style={{ background: 'var(--bg)', color: 'var(--text)' }}>All Seasons</option>
            {yearsActive.map(y => <option key={y} value={y} style={{ background: 'var(--bg)', color: 'var(--text)' }}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* Profile Info Section */}
      <div style={{ padding: '0 2rem 2rem 2rem' }}>
        <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
          <h1 style={{ margin: '0 0 0.5rem 0', fontSize: '2rem' }}>{managerName}</h1>
          <div style={{ color: 'var(--muted)', fontSize: '0.95rem' }}>
            Years Active: {yearsActive.join(', ')} • {overall.wins !== undefined ? formatRecord(overall.wins, overall.losses || 0, overall.ties || 0) : (overall.record || '0-0-0')} Overall
          </div>
        </div>

        {/* Medals */}
        {(medalCounts.gold > 0 || medalCounts.silver > 0 || medalCounts.bronze > 0) && (
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', justifyContent: 'center' }}>
            {medalCounts.gold > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-alt)', padding: '0.5rem 1rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '1.5rem' }}>🥇</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>×{medalCounts.gold}</span>
              </div>
            )}
            {medalCounts.silver > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-alt)', padding: '0.5rem 1rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '1.5rem' }}>🥈</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>×{medalCounts.silver}</span>
              </div>
            )}
            {medalCounts.bronze > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'var(--bg-alt)', padding: '0.5rem 1rem', borderRadius: '8px' }}>
                <span style={{ fontSize: '1.5rem' }}>🥉</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700 }}>×{medalCounts.bronze}</span>
              </div>
            )}
          </div>
        )}

        {/* Quick Stats Horizontal Scroll */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          overflowX: 'auto',
          paddingBottom: '1rem',
          marginBottom: '1.5rem',
          justifyContent: 'center'
        }}>
          <StatCard title="Win %" value={`${overall.win_percentage?.toFixed(1) || 0}%`} />
          <StatCard title="Avg PF" value={overall.average_points_for?.toFixed(2) || 0} />
          <StatCard title="Avg PA" value={overall.average_points_against?.toFixed(2) || 0} />
          <StatCard title="Avg Diff" value={((overall.average_points_for || 0) - (overall.average_points_against || 0)).toFixed(2)} color={((overall.average_points_for || 0) - (overall.average_points_against || 0)) >= 0 ? 'var(--success)' : 'var(--danger)'} />
          <StatCard title="Trades" value={trades.total || 0} />
          <StatCard title="Playoffs" value={playoffAppearances} />
          <StatCard title="Championships" value={championships} color={championships > 0 ? 'var(--accent)' : undefined} />
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '2px solid var(--border)',
          marginBottom: '2rem',
          overflowX: 'auto',
          justifyContent: 'center'
        }}>
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'awards', label: 'Awards' },
            { id: 'transactions', label: 'Transactions' },
            { id: 'weekly', label: 'Weekly Stats', disabled: !year }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              style={{
                padding: '0.75rem 1.5rem',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
                color: tab.disabled ? 'var(--muted)' : activeTab === tab.id ? 'var(--accent)' : 'var(--text)',
                cursor: tab.disabled ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: activeTab === tab.id ? 600 : 400,
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                opacity: tab.disabled ? 0.5 : 1
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
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
        />}

        {activeTab === 'awards' && <AwardsTab
          awardsData={awardsData}
          MatchupCard={MatchupCard}
        />}

        {activeTab === 'transactions' && <TransactionsTab
          transactionHistory={transactionHistory}
          transactionPage={transactionPage}
          setTransactionPage={setTransactionPage}
          totalPages={totalPages}
          transactionsPerPage={transactionsPerPage}
          typeFilter={typeFilter}
          setTypeFilter={setTypeFilter}
        />}

        {activeTab === 'weekly' && year && yearlyData && <WeeklyTab
          yearlyData={yearlyData}
          year={year}
          MatchupCard={MatchupCard}
        />}
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
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: color || 'var(--text)' }}>{value}</div>
    </div>
  );
}

// PlayerLink Component - Displays player with image and clickable link
function PlayerLink({ player, showImage = true }) {
  const playerName = typeof player === 'string' ? player : player?.name || 'Unknown';
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
          to={`/player/${encodeURIComponent(playerName)}`}
          style={{
            color: 'var(--accent)',
            textDecoration: 'none',
            fontWeight: 500
          }}
        >
          {playerName}
        </Link>
      ) : (
        <span style={{ fontWeight: 500, color: 'var(--text)' }}>
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
          color: 'var(--accent)',
          textDecoration: 'none',
          fontWeight: 500
        }}
      >
        {managerName}
      </Link>
    </div>
  );
}

// TradeCard Component - Standardized trade display showing all managers objectively
function TradeCard({ trade }) {
  // Extract managers involved from the trade
  const managersInvolved = trade.managers_involved || [];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${managersInvolved.length}, 1fr)`,
      gap: '2rem'
    }}>
      {managersInvolved.map((manager, idx) => {
        const managerName = typeof manager === 'string' ? manager : manager?.name || 'Unknown';
        const managerKey = managerName.toLowerCase().replace(/\s+/g, '_');
        const received = trade[`${managerKey}_received`] || [];
        const sent = trade[`${managerKey}_sent`] || [];

        return (
          <div key={idx} style={{ textAlign: 'center' }}>
            {/* Manager Name */}
            <div style={{ marginBottom: '1rem', fontSize: '0.95rem', display: 'flex', justifyContent: 'center' }}>
              <ManagerLink manager={manager} showImage={true} />
            </div>

            {/* Received - Emphasized */}
            {received.length > 0 && (
              <div style={{ marginBottom: '1rem' }}>
                <div style={{
                  fontSize: '0.8rem',
                  color: 'var(--success)',
                  marginBottom: '0.75rem',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  Received
                </div>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.5rem',
                  alignItems: 'center'
                }}>
                  {received.map((p, i) => (
                    <PlayerLink key={i} player={p} showImage={true} />
                  ))}
                </div>
              </div>
            )}

            {/* Sent - De-emphasized */}
            {sent.length > 0 && (
              <div style={{
                fontSize: '0.85rem',
                opacity: 0.6
              }}>
                <div style={{
                  fontSize: '0.65rem',
                  color: 'var(--muted)',
                  marginBottom: '0.5rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.3px'
                }}>
                  Sent
                </div>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem',
                  alignItems: 'center'
                }}>
                  {sent.map((p, i) => (
                    <PlayerLink key={i} player={p} showImage={true} />
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Helper function to format records (hide ties if 0)
function formatRecord(wins, losses, ties) {
  if (ties === 0) {
    return `${wins}-${losses}`;
  }
  return `${wins}-${losses}-${ties}`;
}

// Overview Tab
function OverviewTab({ overall, regularSeason, playoffs, trades, adds, drops, faab, placements, headToHead, managerName }) {
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
    <div style={{ display: 'flex', gap: '1.5rem' }}>
      {/* Left Side - 2 Column Flowing Grid */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(2, minmax(auto, 250px))', gap: '0.5rem 0.75rem', alignContent: 'start' }}>
        {/* Season Stats */}
        <Section title="Season Stats">
          <StatRow label="Regular Season" value={regularSeason.wins !== undefined ? formatRecord(regularSeason.wins, regularSeason.losses || 0, regularSeason.ties || 0) : (regularSeason.record || '0-0')} />
          <StatRow label="Playoffs" value={playoffs.wins !== undefined ? formatRecord(playoffs.wins, playoffs.losses || 0, playoffs.ties || 0) : (playoffs.record || '0-0')} />
          <StatRow label="Avg PF" value={overall.average_points_for?.toFixed(2) || 0} />
          <StatRow label="Avg PA" value={overall.average_points_against?.toFixed(2) || 0} />
        </Section>

        {/* Transaction Summary */}
        <Section title="Transactions">
          <StatRow label="Trades" value={trades.total || 0} />
          <StatRow label="Adds" value={adds.total || 0} />
          <StatRow label="Drops" value={drops.total || 0} />
          <StatRow label="FAAB Spent" value={`$${faab.total_spent || 0}`} />
        </Section>

        {/* Placement History */}
        {placements.length > 0 && (
          <Section title="Placements">
            <div>
              {placements.sort((a, b) => b.year - a.year).map((p, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0.05rem 0',
                  maxWidth: '200px',
                  borderBottom: i < placements.length - 1 ? '1px solid var(--border)' : 'none'
                }}>
                  <span>{p.year}</span>
                  <span style={{ fontWeight: 700 }}>
                    {p.placement === 1 && '🥇 Champion'}
                    {p.placement === 2 && '🥈 Runner-up'}
                    {p.placement === 3 && '🥉 3rd Place'}
                    {p.placement > 3 && `${p.placement}th`}
                  </span>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* Top Trade Partners */}
        {trades.top_trade_partners && trades.top_trade_partners.length > 0 && (
          <Section title="Top Trade Partners">
            {trades.top_trade_partners.slice(0, 5).map((partner, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.05rem 0', maxWidth: '200px', fontSize: '0.95rem' }}>
                <ManagerLink manager={partner} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right' }}>{partner.count} trades</span>
              </div>
            ))}
          </Section>
        )}

        {/* Top Players Added */}
        {adds.top_players_added && adds.top_players_added.length > 0 && (
          <Section title="Most Added Players">
            {adds.top_players_added.slice(0, 5).map((player, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.05rem 0', maxWidth: '200px', fontSize: '0.95rem' }}>
                <PlayerLink player={player} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right' }}>×{player.count}</span>
              </div>
            ))}
          </Section>
        )}

        {/* Top Players Dropped */}
        {drops.top_players_dropped && drops.top_players_dropped.length > 0 && (
          <Section title="Most Dropped Players">
            {drops.top_players_dropped.slice(0, 5).map((player, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.05rem 0', maxWidth: '200px', fontSize: '0.95rem' }}>
                <PlayerLink player={player} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right' }}>×{player.count}</span>
              </div>
            ))}
          </Section>
        )}

        {/* Most Acquired via Trade */}
        {trades.most_aquired_players && trades.most_aquired_players.length > 0 && (
          <Section title="Most Acquired (Trade)">
            {trades.most_aquired_players.slice(0, 3).map((player, i) => (
              <div key={i} style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.05rem 0', maxWidth: '200px', fontSize: '0.95rem' }}>
                  <PlayerLink player={player} />
                  <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right' }}>×{player.count}</span>
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
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.05rem 0', maxWidth: '200px', fontSize: '0.95rem' }}>
                  <PlayerLink player={player} />
                  <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right' }}>×{player.count}</span>
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
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.05rem 0', maxWidth: '200px', fontSize: '0.95rem' }}>
                <PlayerLink player={bid} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right' }}>${bid.amount}</span>
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

      {/* Right Sidebar - Head-to-Head */}
      {sortedOpponents.length > 0 && (
        <div style={{ width: '280px', flexShrink: 0 }}>
          <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: 700 }}>Head-to-Head</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
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
                <div
                  key={opponentKey}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                    padding: '0.75rem',
                    background: 'var(--bg-alt)',
                    borderRadius: '8px',
                    border: '1px solid var(--border)',
                    transition: 'all 0.2s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Link
                      to={`/manager/${encodeURIComponent(opponent.name)}`}
                      style={{ flexShrink: 0 }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {opponent.image_url && (
                        <img
                          src={opponent.image_url}
                          alt={opponent.name}
                          style={{
                            width: '56px',
                            height: '56px',
                            borderRadius: '50%',
                            objectFit: 'cover',
                            border: '2px solid var(--border)',
                            cursor: 'pointer'
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                    </Link>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Link
                        to={`/manager/${encodeURIComponent(opponent.name)}`}
                        style={{
                          fontWeight: 600,
                          fontSize: '0.95rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          color: 'var(--accent)',
                          textDecoration: 'none',
                          display: 'block'
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {opponent.name}
                      </Link>
                      <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                        <span>{formatRecord(data.wins, data.losses, data.ties)}</span>
                        {' • '}
                        <span style={{
                          fontWeight: 600,
                          color: parseFloat(winPct) >= 50 ? 'var(--success)' : 'var(--danger)'
                        }}>
                          {winPct}%
                        </span>
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
                        <span>Avg: {avgPointsFor} - {avgPointsAgainst}</span>
                        {tradesCount > 0 && (
                          <>
                            {' • '}
                            <span>{tradesCount} trade{tradesCount !== 1 ? 's' : ''}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <Link
                    to={`/manager/${encodeURIComponent(managerName)}/vs/${encodeURIComponent(opponent.name)}`}
                    style={{
                      fontSize: '0.8rem',
                      color: 'var(--accent)',
                      textDecoration: 'none',
                      fontWeight: 500,
                      display: 'block',
                      paddingLeft: '64px'
                    }}
                  >
                    View details →
                  </Link>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Head-to-Head Matchup Details Page Component
export function HeadToHeadMatchupPage() {
  const { managerName, opponentName } = useParams();
  const navigate = useNavigate();
  const [year, setYear] = useState(null);

  const { data: detailedData, loading } = useHeadToHead(managerName, opponentName, { year });

  // SportsCenter-Style Matchup Card Component (reused from ManagerPage)
  const MatchupCard = ({ matchup, showMargin = false }) => {
    if (!matchup) return null;

    const manager1 = matchup.manager_1 || {};
    const manager2 = matchup.manager_2 || {};
    const manager1Score = matchup.manager_1_score;
    const manager2Score = matchup.manager_2_score;
    const winner = matchup.winner;
    const week = matchup.week;
    const matchupYear = matchup.year;
    const manager1TopScorers = matchup.manager_1_top_3_scorers || [];
    const manager2TopScorers = matchup.manager_2_top_3_scorers || [];

    // Determine result from perspective of manager_1
    let result = 'tie';
    if (winner === manager1.name) result = 'win';
    else if (winner === manager2.name) result = 'loss';

    return (
      <div style={{
        background: 'linear-gradient(135deg, var(--bg-alt) 0%, var(--bg) 100%)',
        borderRadius: '12px',
        border: '2px solid var(--border)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          background: 'var(--bg-alt)',
          padding: '0.5rem 1rem',
          textAlign: 'center',
          color: 'var(--text)',
          fontWeight: 700,
          fontSize: '0.85rem',
          letterSpacing: '0.5px',
          borderBottom: '2px solid var(--border)'
        }}>
          {week && matchupYear ? `Week ${week} ${matchupYear}` : 'Matchup'}
        </div>

        {/* Score Display with Manager Avatars */}
        <div style={{ padding: '1.5rem' }}>
          {/* Manager Avatars + Score Box */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
            {/* Manager 1 Avatar */}
            <Link to={`/manager/${encodeURIComponent(manager1.name)}`} style={{ flexShrink: 0 }}>
              {manager1.image_url && (
                <img
                  src={manager1.image_url}
                  alt={manager1.name}
                  style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '3px solid var(--border)'
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
            </Link>

            {/* Score Box - 2 rows x 2 columns */}
            <div style={{
              flex: 1,
              background: 'var(--bg-alt)',
              border: '2px solid var(--border)',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              {/* Manager 1 Row */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1rem',
                borderBottom: '1px solid var(--border)'
              }}>
                <Link
                  to={`/manager/${encodeURIComponent(manager1.name)}`}
                  style={{
                    flex: 1,
                    fontWeight: 600,
                    fontSize: '1rem',
                    color: result === 'win' ? 'var(--success)' : 'var(--text)',
                    textDecoration: 'none'
                  }}
                >
                  {manager1.name}
                </Link>
                <div style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: result === 'win' ? 'var(--success)' : 'var(--text)',
                  minWidth: '80px',
                  textAlign: 'right'
                }}>
                  {manager1Score?.toFixed(2)}
                </div>
              </div>

              {/* Manager 2 Row */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1rem'
              }}>
                <Link
                  to={`/manager/${encodeURIComponent(manager2.name)}`}
                  style={{
                    flex: 1,
                    fontWeight: 600,
                    fontSize: '1rem',
                    color: result === 'loss' ? 'var(--success)' : 'var(--text)',
                    textDecoration: 'none'
                  }}
                >
                  {manager2.name}
                </Link>
                <div style={{
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: result === 'loss' ? 'var(--success)' : 'var(--text)',
                  minWidth: '80px',
                  textAlign: 'right'
                }}>
                  {manager2Score?.toFixed(2)}
                </div>
              </div>
            </div>

            {/* Manager 2 Avatar */}
            <Link to={`/manager/${encodeURIComponent(manager2.name)}`} style={{ flexShrink: 0 }}>
              {manager2.image_url && (
                <img
                  src={manager2.image_url}
                  alt={manager2.name}
                  style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '3px solid var(--border)'
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
            </Link>
          </div>

          {/* Top 3 Scorers Side by Side */}
          {(manager1TopScorers?.length > 0 || manager2TopScorers?.length > 0) && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              {/* Manager 1 Top Scorers */}
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                  {manager1.name} Top 3
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {manager1TopScorers?.slice(0, 3).map((player, i) => (
                    <div key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem',
                      background: 'var(--bg)',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      fontSize: '0.8rem'
                    }}>
                      {player.image_url && (
                        <img
                          src={player.image_url}
                          alt={player.name}
                          style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '4px',
                            objectFit: 'cover',
                            flexShrink: 0
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Link
                          to={`/player/${encodeURIComponent(player.name)}`}
                          style={{
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            display: 'block',
                            color: 'var(--accent)',
                            textDecoration: 'none'
                          }}
                        >
                          {player.name}
                        </Link>
                        <div style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>
                          {player.position} • {player.score?.toFixed(2)} pts
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Manager 2 Top Scorers */}
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                  {manager2.name} Top 3
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {manager2TopScorers?.slice(0, 3).map((player, i) => (
                    <div key={i} style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      padding: '0.5rem',
                      background: 'var(--bg)',
                      borderRadius: '6px',
                      border: '1px solid var(--border)',
                      fontSize: '0.8rem'
                    }}>
                      {player.image_url && (
                        <img
                          src={player.image_url}
                          alt={player.name}
                          style={{
                            width: '40px',
                            height: '40px',
                            borderRadius: '4px',
                            objectFit: 'cover',
                            flexShrink: 0
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Link
                          to={`/player/${encodeURIComponent(player.name)}`}
                          style={{
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                            display: 'block',
                            color: 'var(--accent)',
                            textDecoration: 'none'
                          }}
                        >
                          {player.name}
                        </Link>
                        <div style={{ fontSize: '0.7rem', color: 'var(--muted)' }}>
                          {player.position} • {player.score?.toFixed(2)} pts
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Margin - Only show for blowouts */}
          {showMargin && matchup.differential !== undefined && (
            <div style={{
              textAlign: 'center',
              fontSize: '0.85rem',
              color: 'var(--muted)',
              paddingTop: '0.75rem',
              marginTop: '0.75rem',
              borderTop: '1px solid var(--border)'
            }}>
              Margin: {Math.abs(matchup.differential).toFixed(2)}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading && !detailedData) {
    return (
      <div className="App" style={{ paddingTop: '2rem' }}>
        <p>Loading head-to-head data...</p>
      </div>
    );
  }

  if (!detailedData) {
    return (
      <div className="App" style={{ paddingTop: '2rem' }}>
        <p style={{ color: 'var(--danger)' }}>No head-to-head data available</p>
      </div>
    );
  }

  const managerKey = managerName.toLowerCase().replace(/\s+/g, '_');
  const opponentKey = opponentName.toLowerCase().replace(/\s+/g, '_');

  // Get manager images from the detailed data
  const manager1Data = detailedData?.overall?.matchup_history?.[0]?.manager_1 || { name: managerName };
  const manager2Data = detailedData?.overall?.matchup_history?.[0]?.manager_2 || { name: opponentName };

  return (
    <div className="App" style={{ paddingTop: 0, maxWidth: '1400px', margin: '0 auto' }}>
      {/* Back Button */}
      <div style={{ padding: '1rem 2rem' }}>
        <button onClick={() => navigate(`/manager/${encodeURIComponent(managerName)}`)} style={{
          background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '1rem', padding: '0.5rem 0'
        }}>← Back to {managerName}</button>
      </div>

      {/* Hero Banner with Manager Pictures */}
      <div style={{
        background: 'linear-gradient(135deg, var(--accent) 0%, var(--bg-alt) 100%)',
        padding: '2rem',
        borderRadius: '0 0 16px 16px',
        marginBottom: '2rem'
      }}>
        {/* Manager Pictures */}
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '3rem', marginBottom: '1.5rem' }}>
          <div style={{ textAlign: 'center' }}>
            {manager1Data.image_url && (
              <img
                src={manager1Data.image_url}
                alt={managerName}
                style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '4px solid white',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
                  marginBottom: '0.5rem'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
            <div style={{ color: 'white', fontWeight: 600, fontSize: '1.1rem' }}>{managerName}</div>
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700, color: 'white' }}>VS</div>
          <div style={{ textAlign: 'center' }}>
            {manager2Data.image_url && (
              <img
                src={manager2Data.image_url}
                alt={opponentName}
                style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '4px solid white',
                  boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
                  marginBottom: '0.5rem'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
            <div style={{ color: 'white', fontWeight: 600, fontSize: '1.1rem' }}>{opponentName}</div>
          </div>
        </div>

        {/* Year Filter */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <select
            value={year || 'ALL'}
            onChange={(e) => setYear(e.target.value === 'ALL' ? null : e.target.value)}
            style={{
              background: 'rgba(255,255,255,0.2)',
              color: 'white',
              border: '1px solid rgba(255,255,255,0.3)',
              padding: '0.5rem 1rem',
              borderRadius: '6px',
              cursor: 'pointer',
              backdropFilter: 'blur(10px)'
            }}
          >
            <option value="ALL" style={{ background: 'var(--bg)', color: 'var(--text)' }}>All Seasons</option>
          </select>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ padding: '0 2rem 2rem 2rem' }}>
        {loading && <p style={{ textAlign: 'center', color: 'var(--muted)' }}>Loading detailed stats...</p>}

        {!loading && detailedData && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '2rem' }}>
            {/* Left Column - Matchup Info */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {/* Overall Record */}
              <div style={{
                padding: '1.5rem',
                background: 'var(--bg-alt)',
                borderRadius: '12px',
                border: '1px solid var(--border)',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>Overall Record</div>
                <div style={{ fontSize: '2.5rem', fontWeight: 700 }}>
                  {formatRecord(detailedData.overall?.wins || 0, detailedData.overall?.losses || 0, detailedData.overall?.ties || 0)}
                </div>
              </div>

            {/* Average Margins of Victory */}
            {(detailedData.overall?.[`${managerKey}_average_margin_of_victory`] !== undefined ||
              detailedData.overall?.[`${opponentKey}_average_margin_of_victory`] !== undefined) && (
              <div>
                <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: 700 }}>Average Margins of Victory</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  {detailedData.overall?.[`${managerKey}_average_margin_of_victory`] !== undefined && (
                    <div style={{ padding: '1.5rem', background: 'var(--bg-alt)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                      <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>{managerName}</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)' }}>
                        +{detailedData.overall[`${managerKey}_average_margin_of_victory`]?.toFixed(2)}
                      </div>
                    </div>
                  )}
                  {detailedData.overall?.[`${opponentKey}_average_margin_of_victory`] !== undefined && (
                    <div style={{ padding: '1.5rem', background: 'var(--bg-alt)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                      <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>{opponentName}</div>
                      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--success)' }}>
                        +{detailedData.overall[`${opponentKey}_average_margin_of_victory`]?.toFixed(2)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Last Wins - Side by Side */}
            <div>
              <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: 700 }}>Most Recent Wins</h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1rem' }}>
                {detailedData.overall?.[`${managerKey}_last_win`] && Object.keys(detailedData.overall[`${managerKey}_last_win`]).length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--muted)' }}>{managerName}'s Last Win</h4>
                    <MatchupCard matchup={detailedData.overall[`${managerKey}_last_win`]} />
                  </div>
                )}
                {detailedData.overall?.[`${opponentKey}_last_win`] && Object.keys(detailedData.overall[`${opponentKey}_last_win`]).length > 0 && (
                  <div>
                    <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--muted)' }}>{opponentName}'s Last Win</h4>
                    <MatchupCard matchup={detailedData.overall[`${opponentKey}_last_win`]} />
                  </div>
                )}
              </div>
            </div>

              {/* Biggest Blowouts */}
              <div>
                <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: 700 }}>Biggest Blowouts</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  {detailedData.overall?.[`${managerKey}_biggest_blowout`] && Object.keys(detailedData.overall[`${managerKey}_biggest_blowout`]).length > 0 && (
                    <div>
                      <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--muted)' }}>{managerName}'s Biggest Blowout</h4>
                      <MatchupCard matchup={detailedData.overall[`${managerKey}_biggest_blowout`]} showMargin={true} />
                    </div>
                  )}
                  {detailedData.overall?.[`${opponentKey}_biggest_blowout`] && Object.keys(detailedData.overall[`${opponentKey}_biggest_blowout`]).length > 0 && (
                    <div>
                      <h4 style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--muted)' }}>{opponentName}'s Biggest Blowout</h4>
                      <MatchupCard matchup={detailedData.overall[`${opponentKey}_biggest_blowout`]} showMargin={true} />
                    </div>
                  )}
                </div>
              </div>

              {/* Matchup History */}
              {detailedData.overall?.matchup_history?.length > 0 && (
                <div>
                  <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: 700 }}>
                    All Matchups ({detailedData.overall.matchup_history.length} games)
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    {detailedData.overall.matchup_history.map((matchup, idx) => (
                      <MatchupCard key={idx} matchup={matchup} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Right Column - Trades */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              {detailedData.trades_between?.total > 0 ? (
                <div style={{
                  padding: '1.5rem',
                  background: 'var(--bg-alt)',
                  borderRadius: '12px',
                  border: '1px solid var(--border)',
                  height: 'fit-content',
                  position: 'sticky',
                  top: '2rem'
                }}>
                  <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 700 }}>
                    Trades Between
                    <span style={{ fontSize: '0.9rem', color: 'var(--muted)', fontWeight: 400, marginLeft: '0.5rem' }}>
                      ({detailedData.trades_between.total} total)
                    </span>
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', maxHeight: '80vh', overflowY: 'auto' }}>
                    {detailedData.trades_between.trade_history?.map((trade, idx) => (
                      <div key={idx} style={{ paddingBottom: '1rem', borderBottom: idx < detailedData.trades_between.trade_history.length - 1 ? '1px solid var(--border)' : 'none' }}>
                        <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem' }}>
                          Week {trade.week}, {trade.year}
                        </div>
                        <TradeCard trade={trade} />
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div style={{
                  padding: '2rem',
                  background: 'var(--bg-alt)',
                  borderRadius: '12px',
                  border: '1px solid var(--border)',
                  textAlign: 'center',
                  color: 'var(--muted)'
                }}>
                  <p>No trades between these managers</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

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
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', textTransform: 'uppercase', fontWeight: 600 }}>
                💰 Biggest FAAB Bid
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '0.5rem' }}>
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
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', textTransform: 'uppercase', fontWeight: 600 }}>
                🔄 Most Trades (Single Season)
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '0.5rem' }}>
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

// Transactions Tab - SportsCenter Style with Filters
function TransactionsTab({ transactionHistory, transactionPage, setTransactionPage, totalPages, transactionsPerPage, typeFilter, setTypeFilter }) {
  // Reset to page 0 when filter changes
  React.useEffect(() => {
    setTransactionPage(0);
  }, [typeFilter, setTransactionPage]);

  if (!transactionHistory) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>Loading transactions...</div>;
  }

  if (!transactionHistory.transactions || transactionHistory.transactions.length === 0) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
      <p>No transactions found</p>
      <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>Total count: {transactionHistory.total_count || 0}</p>
    </div>;
  }

  return (
    <div>
      {/* Filters and Pagination Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
        padding: '1rem',
        background: 'linear-gradient(135deg, var(--bg-alt) 0%, var(--bg) 100%)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        {/* Filter Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {['all', 'trade', 'add', 'drop', 'add_and_or_drop'].map(type => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              style={{
                padding: '0.5rem 1rem',
                background: typeFilter === type ? 'var(--accent)' : 'var(--bg)',
                color: typeFilter === type ? 'white' : 'var(--text)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: typeFilter === type ? 600 : 400,
                textTransform: 'capitalize'
              }}
            >
              {type === 'all' && 'All'}
              {type === 'trade' && '🔄 Trades'}
              {type === 'add' && '➕ Adds'}
              {type === 'drop' && '➖ Drops'}
              {type === 'add_and_or_drop' && '🔄 Add/Drop'}
            </button>
          ))}
        </div>

        {/* Pagination */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginRight: '0.5rem' }}>
            {transactionPage * transactionsPerPage + 1}-{Math.min((transactionPage + 1) * transactionsPerPage, transactionHistory.total_count)} of {transactionHistory.total_count}
          </div>
          <button
            onClick={() => setTransactionPage(Math.max(0, transactionPage - 1))}
            disabled={transactionPage === 0}
            style={{
              padding: '0.5rem 0.75rem',
              background: transactionPage === 0 ? 'var(--bg)' : 'var(--accent)',
              color: transactionPage === 0 ? 'var(--muted)' : 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: transactionPage === 0 ? 'not-allowed' : 'pointer',
              fontSize: '0.85rem'
            }}
          >
            ←
          </button>
          <div style={{ padding: '0.5rem 0.75rem', background: 'var(--bg)', borderRadius: '6px', fontSize: '0.85rem', minWidth: '80px', textAlign: 'center' }}>
            {transactionPage + 1} / {totalPages}
          </div>
          <button
            onClick={() => setTransactionPage(Math.min(totalPages - 1, transactionPage + 1))}
            disabled={transactionPage >= totalPages - 1}
            style={{
              padding: '0.5rem 0.75rem',
              background: transactionPage >= totalPages - 1 ? 'var(--bg)' : 'var(--accent)',
              color: transactionPage >= totalPages - 1 ? 'var(--muted)' : 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: transactionPage >= totalPages - 1 ? 'not-allowed' : 'pointer',
              fontSize: '0.85rem'
            }}
          >
            →
          </button>
        </div>
      </div>

      {/* Transaction Feed */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {transactionHistory.transactions.map((txn, i) => (
          <div key={i} style={{
            paddingBottom: '1rem',
            borderBottom: '1px solid var(--border)'
          }}>
            {/* Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.75rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: 'var(--muted)' }}>
                <span>
                  {txn.type === 'trade' && '🔄 Trade'}
                  {txn.type === 'add' && '➕ Add'}
                  {txn.type === 'drop' && '➖ Drop'}
                  {txn.type === 'add_and_or_drop' && '🔄 Add/Drop'}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                Week {txn.week} • {txn.year}
              </div>
            </div>

            {/* Content */}
            <div>
              {txn.type === 'trade' && (
                <TradeCard trade={txn} />
              )}
              {txn.type === 'add' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <PlayerLink player={txn.player} showImage={true} />
                  {txn.faab_spent !== null && txn.faab_spent !== undefined && (
                    <span style={{ fontSize: '0.9rem', color: 'var(--success)', fontWeight: 700 }}>
                      ${txn.faab_spent} FAAB
                    </span>
                  )}
                </div>
              )}
              {txn.type === 'drop' && (
                <PlayerLink player={txn.player} showImage={true} />
              )}
              {txn.type === 'add_and_or_drop' && (
                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.95rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--success)', fontSize: '0.8rem' }}>Added:</span>
                    <PlayerLink player={txn.added_player} showImage={true} />
                    {txn.faab_spent !== null && txn.faab_spent !== undefined && (
                      <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                        (${txn.faab_spent})
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--danger)', fontSize: '0.8rem' }}>Dropped:</span>
                    <PlayerLink player={txn.dropped_player} showImage={true} />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Weekly Stats Tab - Compact grid layout
function WeeklyTab({ yearlyData, year, MatchupCard }) {
  if (!yearlyData) return null;

  const weeklyScores = yearlyData.matchup_data?.overall?.weekly_scores || [];
  const tradesByWeek = yearlyData.transactions?.trades?.by_week || [];
  const addsByWeek = yearlyData.transactions?.adds?.by_week || [];
  const dropsByWeek = yearlyData.transactions?.drops?.by_week || [];

  // Filter out weeks where the manager didn't play (empty matchup_data)
  const validWeeklyScores = weeklyScores.filter(week =>
    week.manager_1 && week.manager_2 && week.manager_1_score !== undefined && week.manager_2_score !== undefined
  );

  return (
    <div>
      <h3 style={{ marginBottom: '1.5rem' }}>Week-by-Week Breakdown for {year}</h3>

      {/* Weekly Matchups in 2-column grid */}
      {validWeeklyScores.length > 0 && (
        <Section title="📅 Weekly Matchups">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1rem' }}>
            {validWeeklyScores.map((matchup, i) => (
              <MatchupCard
                key={i}
                matchup={matchup}
              />
            ))}
          </div>
        </Section>
      )}

      {/* Weekly Trades */}
      {tradesByWeek.length > 0 && tradesByWeek.some(w => w.trades && w.trades.length > 0) && (
        <Section title="🔄 Trades by Week" style={{ marginTop: '2rem' }}>
          {tradesByWeek.filter(w => w.trades && w.trades.length > 0).map((weekData, i) => (
            <div key={i} style={{ marginBottom: '1rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent)' }}>Week {weekData.week}</div>
              {weekData.trades.map((trade, j) => (
                <div key={j} style={{
                  paddingBottom: '0.75rem',
                  marginBottom: '0.75rem',
                  borderBottom: j < weekData.trades.length - 1 ? '1px solid var(--border)' : 'none'
                }}>
                  <TradeCard trade={trade} />
                </div>
              ))}
            </div>
          ))}
        </Section>
      )}

      {/* Weekly Adds */}
      {addsByWeek.length > 0 && addsByWeek.some(w => w.players && w.players.length > 0) && (
        <Section title="➕ Adds by Week" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.75rem' }}>
            {addsByWeek.filter(w => w.players && w.players.length > 0).map((weekData, i) => (
              <div key={i} style={{
                padding: '0.75rem',
                background: 'var(--bg-alt)',
                borderRadius: '6px',
                border: '1px solid var(--border)'
              }}>
                <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.85rem' }}>Week {weekData.week}</div>
                <div style={{ fontSize: '0.8rem' }}>
                  {weekData.players.map((p, j) => <div key={j}>{typeof p === 'string' ? p : p?.name || 'Unknown Player'}</div>)}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Weekly Drops */}
      {dropsByWeek.length > 0 && dropsByWeek.some(w => w.players && w.players.length > 0) && (
        <Section title="➖ Drops by Week" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.75rem' }}>
            {dropsByWeek.filter(w => w.players && w.players.length > 0).map((weekData, i) => (
              <div key={i} style={{
                padding: '0.75rem',
                background: 'var(--bg-alt)',
                borderRadius: '6px',
                border: '1px solid var(--border)'
              }}>
                <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.85rem' }}>Week {weekData.week}</div>
                <div style={{ fontSize: '0.8rem' }}>
                  {weekData.players.map((p, j) => <div key={j}>{typeof p === 'string' ? p : p?.name || 'Unknown Player'}</div>)}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// Section Component
function Section({ title, children, style }) {
  return (
    <div style={{ ...style }}>
      <h3 style={{ marginBottom: '0.1rem', fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>{title}</h3>
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
      padding: '0.05rem 0',
      fontSize: small ? '0.85rem' : '0.95rem',
      maxWidth: '200px'
    }}>
      <span style={{ color: 'var(--muted)' }}>{label}</span>
      <span style={{ fontWeight: 600, color: color || 'var(--text)' }}>{value}</span>
    </div>
  );
}
