import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useManagerSummary } from '../hooks/useManagerSummary';
import { useManagerAwards } from '../hooks/useManagerAwards';
import { useManagerTransactions } from '../hooks/useManagerTransactions';
import { useManagerYearlyData } from '../hooks/useManagerYearlyData';

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
  const transactionsPerPage = 20;

  // Fetch data from ALL endpoints
  const { summary, loading: summaryLoading, error: summaryError } = useManagerSummary(managerName, { year });
  const { awards, loading: awardsLoading } = useManagerAwards(managerName);
  const { transactions: transactionHistory, loading: transactionsLoading } = useManagerTransactions(
    managerName,
    { year, limit: transactionsPerPage, offset: transactionPage * transactionsPerPage }
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
          background: result === 'win' ? 'linear-gradient(90deg, #4CAF50 0%, #388E3C 100%)' :
                      result === 'loss' ? 'linear-gradient(90deg, #f44336 0%, #D32F2F 100%)' :
                      'linear-gradient(90deg, #9E9E9E 0%, #757575 100%)',
          padding: '0.5rem 1rem',
          textAlign: 'center',
          color: 'white',
          fontWeight: 700,
          fontSize: '0.85rem',
          letterSpacing: '0.5px',
          textTransform: 'uppercase'
        }}>
          {week && year && `Week ${week} ${year} • `}
          {result === 'win' ? 'WIN' : result === 'loss' ? 'LOSS' : result === 'tie' ? 'TIE' : 'FINAL'}
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
                borderBottom: '1px solid var(--border)',
                background: result === 'win' ? 'rgba(76, 175, 80, 0.1)' : 'transparent'
              }}>
                <Link
                  to={`/manager/${encodeURIComponent(manager1.name)}`}
                  style={{
                    flex: 1,
                    fontWeight: 600,
                    fontSize: '1rem',
                    color: 'var(--text)',
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
                padding: '1rem',
                background: result === 'loss' ? 'rgba(76, 175, 80, 0.1)' : 'transparent'
              }}>
                <Link
                  to={`/manager/${encodeURIComponent(manager2.name)}`}
                  style={{
                    flex: 1,
                    fontWeight: 600,
                    fontSize: '1rem',
                    color: 'var(--text)',
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
                            width: '32px',
                            height: '32px',
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
                            width: '32px',
                            height: '32px',
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
            Years Active: {yearsActive.join(', ')} • {overall.record || '0-0-0'} Overall
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
          marginBottom: '1.5rem'
        }}>
          <StatCard title="Win %" value={`${overall.win_percentage?.toFixed(1) || 0}%`} />
          <StatCard title="PF" value={overall.total_points_for?.toFixed(2) || 0} />
          <StatCard title="PA" value={overall.total_points_against?.toFixed(2) || 0} />
          <StatCard title="Diff" value={(overall.point_differential || 0).toFixed(2)} color={(overall.point_differential || 0) >= 0 ? 'var(--success)' : 'var(--danger)'} />
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
          overflowX: 'auto'
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

// Overview Tab
function OverviewTab({ overall, regularSeason, playoffs, trades, adds, drops, faab, placements, headToHead }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
      {/* Matchup Stats */}
      <Section title="📊 Season Stats">
        <StatRow label="Regular Season" value={regularSeason.record || '0-0-0'} />
        <StatRow label="Playoffs" value={playoffs.record || '0-0-0'} />
        <StatRow label="Avg PF" value={overall.average_points_for?.toFixed(2) || 0} />
        <StatRow label="Avg PA" value={overall.average_points_against?.toFixed(2) || 0} />
      </Section>

      {/* Transaction Summary */}
      <Section title="💼 Transactions">
        <StatRow label="Trades" value={trades.total || 0} />
        <StatRow label="Adds" value={adds.total || 0} />
        <StatRow label="Drops" value={drops.total || 0} />
        <StatRow label="FAAB Spent" value={`$${faab.total_spent || 0}`} />
      </Section>

      {/* Placement History */}
      {placements.length > 0 && (
        <Section title="📅 Placements">
          <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
            {placements.sort((a, b) => b.year - a.year).map((p, i) => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '0.5rem 0',
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
        <Section title="🤝 Top Trade Partners">
          {trades.top_trade_partners.slice(0, 5).map((partner, i) => (
            <StatRow key={i} label={typeof partner.name === 'string' ? partner.name : partner.name?.name || 'Unknown'} value={`${partner.count} trades`} />
          ))}
        </Section>
      )}

      {/* Top Players Added - NEW */}
      {adds.top_players_added && adds.top_players_added.length > 0 && (
        <Section title="➕ Most Added Players">
          {adds.top_players_added.slice(0, 5).map((player, i) => (
            <StatRow key={i} label={typeof player.name === 'string' ? player.name : player.name?.name || 'Unknown'} value={`×${player.count}`} />
          ))}
        </Section>
      )}

      {/* Top Players Dropped - NEW */}
      {drops.top_players_dropped && drops.top_players_dropped.length > 0 && (
        <Section title="➖ Most Dropped Players">
          {drops.top_players_dropped.slice(0, 5).map((player, i) => (
            <StatRow key={i} label={typeof player.name === 'string' ? player.name : player.name?.name || 'Unknown'} value={`×${player.count}`} />
          ))}
        </Section>
      )}

      {/* Most Acquired via Trade */}
      {trades.most_aquired_players && trades.most_aquired_players.length > 0 && (
        <Section title="📈 Most Acquired (Trade)">
          {trades.most_aquired_players.slice(0, 3).map((player, i) => (
            <div key={i} style={{ marginBottom: '0.75rem' }}>
              <StatRow label={typeof player.name === 'string' ? player.name : player.name?.name || 'Unknown'} value={`×${player.count}`} />
              {player.from && player.from.length > 0 && (
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem', paddingLeft: '0.5rem' }}>
                  From: {player.from.map(m => `${m.name} (${m.count})`).join(', ')}
                </div>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* Most Sent via Trade */}
      {trades.most_sent_players && trades.most_sent_players.length > 0 && (
        <Section title="📉 Most Sent (Trade)">
          {trades.most_sent_players.slice(0, 3).map((player, i) => (
            <div key={i} style={{ marginBottom: '0.75rem' }}>
              <StatRow label={typeof player.name === 'string' ? player.name : player.name?.name || 'Unknown'} value={`×${player.count}`} />
              {player.to && player.to.length > 0 && (
                <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem', paddingLeft: '0.5rem' }}>
                  To: {player.to.map(m => `${m.name} (${m.count})`).join(', ')}
                </div>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* FAAB Biggest Acquisitions */}
      {faab.biggest_acquisitions && faab.biggest_acquisitions.length > 0 && (
        <Section title="💰 Biggest FAAB Bids">
          {faab.biggest_acquisitions.map((bid, i) => (
            <StatRow key={i} label={typeof bid.name === 'string' ? bid.name : bid.name?.name || 'Unknown'} value={`$${bid.amount}`} />
          ))}
        </Section>
      )}

      {/* FAAB Traded */}
      {faab.faab_traded && (
        <Section title="💸 FAAB Trading">
          <StatRow label="Sent" value={`$${faab.faab_traded.sent || 0}`} color="var(--danger)" />
          <StatRow label="Received" value={`$${faab.faab_traded.received || 0}`} color="var(--success)" />
          <StatRow label="Net" value={`$${faab.faab_traded.net || 0}`} color={faab.faab_traded.net > 0 ? 'var(--success)' : faab.faab_traded.net < 0 ? 'var(--danger)' : undefined} />
        </Section>
      )}

      {/* Head-to-Head Full Width */}
      {Object.keys(headToHead).length > 0 && (
        <div style={{ gridColumn: '1 / -1' }}>
          <Section title="⚔️ Head-to-Head Records">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
              {Object.entries(headToHead).sort((a, b) => b[1].wins - a[1].wins).map(([opponentKey, data]) => {
                const opponent = data.opponent || { name: opponentKey };
                return (
                  <div key={opponentKey} style={{
                    padding: '1rem',
                    background: 'var(--bg)',
                    borderRadius: '8px',
                    border: '1px solid var(--border)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                      {opponent.image_url && (
                        <img
                          src={opponent.image_url}
                          alt={opponent.name}
                          style={{
                            width: '32px',
                            height: '32px',
                            borderRadius: '50%',
                            objectFit: 'cover',
                            border: '2px solid var(--border)'
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                      <div style={{ fontWeight: 700 }}>{opponent.name}</div>
                    </div>
                    <StatRow label="Record" value={`${data.wins}-${data.losses}-${data.ties}`} small />
                    <StatRow label="Win%" value={`${((data.wins / (data.wins + data.losses + data.ties || 1)) * 100).toFixed(1)}%`} small />
                    <StatRow label="PF" value={data.points_for?.toFixed(2) || 0} small />
                    <StatRow label="PA" value={data.points_against?.toFixed(2) || 0} small />
                  </div>
                );
              })}
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}

// Awards Tab - Using MatchupCard for all matchup awards
function AwardsTab({ awardsData, MatchupCard }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
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

      {/* Biggest FAAB Bid */}
      {awardsData.biggest_faab_bid && awardsData.biggest_faab_bid.amount > 0 && (
        <AwardCard
          title="💰 Biggest FAAB Bid"
          value={`$${awardsData.biggest_faab_bid.amount}`}
          subtitle={`${awardsData.biggest_faab_bid.player?.name || awardsData.biggest_faab_bid.player} (${awardsData.biggest_faab_bid.year})`}
          color="var(--accent)"
        />
      )}

      {/* Most Trades in Year */}
      {awardsData.most_trades_in_year && awardsData.most_trades_in_year.count > 0 && (
        <AwardCard
          title="🔄 Most Trades (Single Season)"
          value={awardsData.most_trades_in_year.count}
          subtitle={awardsData.most_trades_in_year.year}
          color="var(--accent)"
        />
      )}
    </div>
  );
}

// Award Card Component
function AwardCard({ title, value, subtitle, color, topScorers, TopScorers, managerName }) {
  return (
    <div style={{
      padding: '1.5rem',
      background: 'var(--bg-alt)',
      borderRadius: '12px',
      border: '1px solid var(--border)'
    }}>
      <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', textTransform: 'uppercase', fontWeight: 600 }}>
        {title}
      </div>
      <div style={{ fontSize: '2.5rem', fontWeight: 700, color: color || 'var(--text)', marginBottom: '0.5rem' }}>
        {value}
      </div>
      <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
        {subtitle}
      </div>
      {topScorers && TopScorers && managerName && (
        <TopScorers scorers={topScorers} managerName={managerName} />
      )}
    </div>
  );
}

// Transactions Tab - SportsCenter Style with Filters
function TransactionsTab({ transactionHistory, transactionPage, setTransactionPage, totalPages, transactionsPerPage }) {
  const [typeFilter, setTypeFilter] = React.useState('all');

  if (!transactionHistory || !transactionHistory.transactions) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>No transactions found</div>;
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
          {['all', 'trade', 'add', 'drop', 'add_and_drop'].map(type => (
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
              {type === 'add_and_drop' && '🔄 Add/Drop'}
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

      {/* Transaction Feed - SportsCenter Style */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {transactionHistory.transactions
          .filter(txn => typeFilter === 'all' || txn.type === typeFilter)
          .map((txn, i) => (
          <div key={i} style={{
            background: 'linear-gradient(135deg, var(--bg-alt) 0%, var(--bg) 50%)',
            borderRadius: '12px',
            border: '2px solid var(--border)',
            overflow: 'hidden',
            position: 'relative'
          }}>
            {/* Header Bar - SportsCenter Style */}
            <div style={{
              background: txn.type === 'trade' ? 'linear-gradient(90deg, #4a90e2 0%, #357ABD 100%)' :
                          txn.type === 'add' ? 'linear-gradient(90deg, #4CAF50 0%, #388E3C 100%)' :
                          txn.type === 'drop' ? 'linear-gradient(90deg, #f44336 0%, #D32F2F 100%)' :
                          'linear-gradient(90deg, #FF9800 0%, #F57C00 100%)',
              padding: '0.75rem 1rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              color: 'white'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.25rem' }}>
                  {txn.type === 'trade' && '🔄'}
                  {txn.type === 'add' && '➕'}
                  {txn.type === 'drop' && '➖'}
                  {txn.type === 'add_and_drop' && '🔄'}
                </span>
                <span style={{ fontWeight: 700, textTransform: 'uppercase', fontSize: '0.9rem', letterSpacing: '0.5px' }}>
                  {txn.type === 'trade' && 'Trade'}
                  {txn.type === 'add' && 'Acquisition'}
                  {txn.type === 'drop' && 'Released'}
                  {txn.type === 'add_and_drop' && 'Swap'}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', opacity: 0.9 }}>
                Week {txn.week} • {txn.year}
              </div>
            </div>

            {/* Content */}
            <div style={{ padding: '1rem' }}>
              {txn.type === 'trade' && (
                <div>
                  <div style={{ marginBottom: '0.75rem', fontSize: '0.9rem', color: 'var(--muted)' }}>
                    Trade Partners: <span style={{ color: 'var(--text)', fontWeight: 600 }}>
                      {txn.partners?.map(p => typeof p === 'string' ? p : p?.name || 'Unknown').join(', ')}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div style={{ padding: '0.75rem', background: 'var(--bg-alt)', borderRadius: '8px', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--success)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                        Acquired
                      </div>
                      <div style={{ fontSize: '0.9rem' }}>
                        {txn.acquired?.map(p => typeof p === 'string' ? p : p?.name || 'Unknown').join(', ')}
                      </div>
                    </div>
                    <div style={{ padding: '0.75rem', background: 'var(--bg-alt)', borderRadius: '8px', border: '1px solid rgba(244, 67, 54, 0.3)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--danger)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                        Sent
                      </div>
                      <div style={{ fontSize: '0.9rem' }}>
                        {txn.sent?.map(p => typeof p === 'string' ? p : p?.name || 'Unknown').join(', ')}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              {txn.type === 'add' && (
                <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>
                  {typeof txn.player === 'string' ? txn.player : txn.player?.name || 'Unknown Player'}
                  {txn.faab_spent !== null && txn.faab_spent !== undefined && (
                    <span style={{ marginLeft: '0.75rem', fontSize: '0.9rem', color: 'var(--success)', fontWeight: 700 }}>
                      ${txn.faab_spent} FAAB
                    </span>
                  )}
                </div>
              )}
              {txn.type === 'drop' && (
                <div style={{ fontSize: '1.1rem', fontWeight: 600, color: 'var(--danger)' }}>
                  {typeof txn.player === 'string' ? txn.player : txn.player?.name || 'Unknown Player'}
                </div>
              )}
              {txn.type === 'add_and_drop' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div style={{ padding: '0.75rem', background: 'var(--bg-alt)', borderRadius: '8px', border: '1px solid rgba(76, 175, 80, 0.3)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--success)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                      Added
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 600 }}>
                      {typeof txn.added_player === 'string' ? txn.added_player : txn.added_player?.name || 'Unknown Player'}
                      {txn.faab_spent !== null && txn.faab_spent !== undefined && (
                        <span style={{ marginLeft: '0.5rem', fontSize: '0.85rem', color: 'var(--success)' }}>
                          (${txn.faab_spent})
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{ padding: '0.75rem', background: 'var(--bg-alt)', borderRadius: '8px', border: '1px solid rgba(244, 67, 54, 0.3)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--danger)', marginBottom: '0.5rem', textTransform: 'uppercase', fontWeight: 600 }}>
                      Dropped
                    </div>
                    <div style={{ fontSize: '1rem', fontWeight: 600 }}>
                      {typeof txn.dropped_player === 'string' ? txn.dropped_player : txn.dropped_player?.name || 'Unknown Player'}
                    </div>
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

// Weekly Stats Tab - Using MatchupCard and filtering out empty matchups
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

      {/* Weekly Scores - SportsCenter Style with MatchupCard */}
      <Section title="📅 Weekly Matchups">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '1rem' }}>
          {validWeeklyScores.map((matchup, i) => (
            <MatchupCard
              key={i}
              matchup={matchup}
            />
          ))}
        </div>
      </Section>

      {/* Weekly Trades - NEW */}
      {tradesByWeek.length > 0 && tradesByWeek.some(w => w.trades && w.trades.length > 0) && (
        <Section title="🔄 Trades by Week" style={{ marginTop: '2rem' }}>
          {tradesByWeek.filter(w => w.trades && w.trades.length > 0).map((weekData, i) => (
            <div key={i} style={{ marginBottom: '1rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.5rem', color: 'var(--accent)' }}>Week {weekData.week}</div>
              {weekData.trades.map((trade, j) => (
                <div key={j} style={{
                  padding: '0.75rem',
                  background: 'var(--bg-alt)',
                  borderRadius: '6px',
                  marginBottom: '0.5rem',
                  border: '1px solid var(--border)',
                  fontSize: '0.9rem'
                }}>
                  <div><strong>With:</strong> {trade.partners?.map(p => typeof p === 'string' ? p : p?.name || 'Unknown').join(', ')}</div>
                  <div><strong>Got:</strong> {trade.acquired?.map(p => typeof p === 'string' ? p : p?.name || 'Unknown').join(', ')}</div>
                  <div><strong>Sent:</strong> {trade.sent?.map(p => typeof p === 'string' ? p : p?.name || 'Unknown').join(', ')}</div>
                </div>
              ))}
            </div>
          ))}
        </Section>
      )}

      {/* Weekly Adds - NEW */}
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

      {/* Weekly Drops - NEW */}
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
      <h3 style={{ marginBottom: '1rem', fontSize: '1.1rem', color: 'var(--text)' }}>{title}</h3>
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
      padding: '0.5rem 0',
      fontSize: small ? '0.85rem' : '0.95rem'
    }}>
      <span style={{ color: 'var(--muted)' }}>{label}</span>
      <span style={{ fontWeight: 600, color: color || 'var(--text)' }}>{value}</span>
    </div>
  );
}
