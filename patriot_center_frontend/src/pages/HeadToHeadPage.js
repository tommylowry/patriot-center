import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useHeadToHead } from '../hooks/useHeadToHead';
import { MatchupCard } from '../components/MatchupCard';
import { TradeCard } from '../components/TradeCard';

/**
 * HeadToHeadPage - Clean, flowing head-to-head rivalry page
 * Minimal boxes, clean aesthetic inspired by Overview page
 */
export default function HeadToHeadPage() {
  const [searchParams] = useSearchParams();
  const manager1 = searchParams.get('manager1');
  const manager2 = searchParams.get('manager2');
  const year = searchParams.get('year');

  const { data, loading, error } = useHeadToHead(manager1, manager2, { year });

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
  const matchupHistory = overall.matchup_history || [];

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
    <div className="App" style={{ paddingTop: '1rem', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
      {/* Two-column layout with managers and their stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr auto 1fr',
        gap: '4rem',
        marginBottom: '3rem',
        paddingBottom: '2rem',
        borderBottom: '1px solid var(--border)'
      }}>
        {/* Manager 1 Side */}
        <div>
          {/* Manager 1 Info */}
          <Link
            to={`/manager/${encodeURIComponent(m1.name)}`}
            style={{
              textDecoration: 'none',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginBottom: '2rem'
            }}
          >
            {m1.image_url && (
              <img
                src={m1.image_url}
                alt={m1.name}
                style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '3px solid var(--border)',
                  marginBottom: '1rem'
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
              marginBottom: '0.5rem'
            }}>
              {m1.name}
            </div>
            <div style={{
              fontSize: '3rem',
              fontWeight: 700,
              color: m1Wins > m2Wins ? 'var(--success)' : 'var(--text)',
              lineHeight: 1
            }}>
              {m1Wins}
            </div>
            <div style={{
              fontSize: '0.75rem',
              color: 'var(--muted)',
              fontWeight: 600,
              marginTop: '0.5rem'
            }}>
              {m1WinPct}% WIN RATE
            </div>
          </Link>

          {/* Manager 1 Stats */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <StatRow
              label="Avg Margin"
              value={m1AvgMargin.toFixed(1)}
              highlight={m1AvgMargin > m2AvgMargin}
            />
            <StatRow
              label="Avg Points/Game"
              value={(totalGames > 0 ? m1PointsFor / totalGames : 0).toFixed(1)}
              highlight={(m1PointsFor / totalGames) > (m2PointsFor / totalGames)}
            />
          </div>
        </div>

        {/* Center - VS */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '0 1rem'
        }}>
          <div style={{
            fontSize: '2rem',
            fontWeight: 700,
            color: 'var(--muted)',
            marginBottom: '0.5rem'
          }}>
            VS
          </div>
          <div style={{
            fontSize: '0.8rem',
            color: 'var(--muted)',
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}>
            {totalGames} {totalGames === 1 ? 'Game' : 'Games'}
          </div>
          {ties > 0 && (
            <div style={{
              fontSize: '0.7rem',
              color: 'var(--muted)',
              marginTop: '0.25rem'
            }}>
              {ties} {ties === 1 ? 'Tie' : 'Ties'}
            </div>
          )}
        </div>

        {/* Manager 2 Side */}
        <div>
          {/* Manager 2 Info */}
          <Link
            to={`/manager/${encodeURIComponent(m2.name)}`}
            style={{
              textDecoration: 'none',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginBottom: '2rem'
            }}
          >
            {m2.image_url && (
              <img
                src={m2.image_url}
                alt={m2.name}
                style={{
                  width: '100px',
                  height: '100px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '3px solid var(--border)',
                  marginBottom: '1rem'
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
              marginBottom: '0.5rem'
            }}>
              {m2.name}
            </div>
            <div style={{
              fontSize: '3rem',
              fontWeight: 700,
              color: m2Wins > m1Wins ? 'var(--success)' : 'var(--text)',
              lineHeight: 1
            }}>
              {m2Wins}
            </div>
            <div style={{
              fontSize: '0.75rem',
              color: 'var(--muted)',
              fontWeight: 600,
              marginTop: '0.5rem'
            }}>
              {m2WinPct}% WIN RATE
            </div>
          </Link>

          {/* Manager 2 Stats */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <StatRow
              label="Avg Margin"
              value={m2AvgMargin.toFixed(1)}
              highlight={m2AvgMargin > m1AvgMargin}
            />
            <StatRow
              label="Avg Points/Game"
              value={(totalGames > 0 ? m2PointsFor / totalGames : 0).toFixed(1)}
              highlight={(m2PointsFor / totalGames) > (m1PointsFor / totalGames)}
            />
          </div>
        </div>
      </div>

      {/* Trades Between */}
      {totalTrades > 0 && (
        <div style={{
          textAlign: 'center',
          paddingBottom: '2rem',
          marginBottom: '3rem',
          borderBottom: '1px solid var(--border)'
        }}>
          <div style={{
            fontSize: '0.7rem',
            fontWeight: 600,
            color: 'var(--muted)',
            marginBottom: '0.5rem',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Trades Between
          </div>
          <div style={{
            fontSize: '2.5rem',
            fontWeight: 700,
            color: 'var(--text)',
            lineHeight: 1
          }}>
            {totalTrades}
          </div>
        </div>
      )}

      {/* Notable Matchups */}
      {(m1LastWin || m2LastWin || m1BiggestBlowout || m2BiggestBlowout) && (
        <div style={{ marginBottom: '3rem' }}>
          <h2 style={{
            fontSize: '1.3rem',
            fontWeight: 700,
            marginBottom: '1.5rem',
            color: 'var(--text)'
          }}>
            Notable Matchups
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '2rem'
          }}>
            {m1LastWin && Object.keys(m1LastWin).length > 0 && (
              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: 'var(--muted)',
                  marginBottom: '0.75rem'
                }}>
                  {m1.name}'s Last Win
                </div>
                <MatchupCard matchup={m1LastWin} showMargin={false} hideHeader={true} />
              </div>
            )}
            {m2LastWin && Object.keys(m2LastWin).length > 0 && (
              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: 'var(--muted)',
                  marginBottom: '0.75rem'
                }}>
                  {m2.name}'s Last Win
                </div>
                <MatchupCard matchup={m2LastWin} showMargin={false} hideHeader={true} />
              </div>
            )}
            {m1BiggestBlowout && Object.keys(m1BiggestBlowout).length > 0 && (
              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: 'var(--muted)',
                  marginBottom: '0.75rem'
                }}>
                  {m1.name}'s Biggest Blowout
                </div>
                <MatchupCard matchup={m1BiggestBlowout} showMargin={true} hideHeader={true} />
              </div>
            )}
            {m2BiggestBlowout && Object.keys(m2BiggestBlowout).length > 0 && (
              <div>
                <div style={{
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  color: 'var(--muted)',
                  marginBottom: '0.75rem'
                }}>
                  {m2.name}'s Biggest Blowout
                </div>
                <MatchupCard matchup={m2BiggestBlowout} showMargin={true} hideHeader={true} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Matchup History */}
      {matchupHistory.length > 0 && (
        <div style={{ marginBottom: '3rem' }}>
          <h2 style={{
            fontSize: '1.3rem',
            fontWeight: 700,
            marginBottom: '1.5rem',
            color: 'var(--text)'
          }}>
            All Matchups ({matchupHistory.length})
          </h2>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '1.5rem'
          }}>
            {matchupHistory.map((matchup, idx) => (
              <div key={idx}>
                <div style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'var(--muted)',
                  marginBottom: '0.5rem'
                }}>
                  Week {matchup.week} • {matchup.year}
                </div>
                <MatchupCard matchup={matchup} hideHeader={true} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trade History */}
      {tradeHistory.length > 0 && (
        <div style={{ marginBottom: '3rem' }}>
          <h2 style={{
            fontSize: '1.3rem',
            fontWeight: 700,
            marginBottom: '1.5rem',
            color: 'var(--text)'
          }}>
            Trades ({totalTrades})
          </h2>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '1.5rem'
          }}>
            {tradeHistory.map((trade, idx) => (
              <div key={idx}>
                <div style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'var(--muted)',
                  marginBottom: '0.5rem'
                }}>
                  Week {trade.week} {trade.year}
                </div>
                <TradeCard trade={trade} hideHeader={true} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// StatRow - Individual stat display
function StatRow({ label, value, highlight }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.75rem 0',
      borderBottom: '1px solid var(--border)'
    }}>
      <div style={{
        fontSize: '0.8rem',
        fontWeight: 600,
        color: 'var(--muted)',
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        {label}
      </div>
      <div style={{
        fontSize: '1.5rem',
        fontWeight: 700,
        color: highlight ? 'var(--success)' : 'var(--text)'
      }}>
        {value}
      </div>
    </div>
  );
}
