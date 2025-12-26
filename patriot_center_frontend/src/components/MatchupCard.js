import React from 'react';
import { Link } from 'react-router-dom';

/**
 * MatchupCard - Sports broadcast style matchup display
 * Inspired by hockey/football broadcast graphics with team logos, scores, and player stats
 */
export function MatchupCard({ matchup, showMargin = false, hideHeader = false }) {
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
  const manager1LowestScorer = matchup.manager_1_lowest_scorer;
  const manager2LowestScorer = matchup.manager_2_lowest_scorer;

  // Combine top scorers with lowest scorer
  const manager1Players = [...manager1TopScorers];
  if (manager1LowestScorer) manager1Players.push(manager1LowestScorer);

  const manager2Players = [...manager2TopScorers];
  if (manager2LowestScorer) manager2Players.push(manager2LowestScorer);

  const manager1Won = winner === manager1.name;
  const manager2Won = winner === manager2.name;

  return (
    <div style={{
      borderRadius: '8px',
      overflow: 'hidden',
      border: '1px solid var(--border)',
      maxWidth: '900px',
      width: '100%'
    }}>
      {/* Top Section - Title Only */}
      {!hideHeader && week && year && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          marginBottom: '0.25rem'
        }}>
          <div style={{
            padding: '0.6rem 1rem 0.4rem 1rem',
            fontSize: '1rem',
            fontWeight: 700,
            letterSpacing: '1.5px',
            textTransform: 'uppercase',
            color: 'var(--text)',
            borderLeft: '1px solid var(--border)',
            borderRight: '1px solid var(--border)',
            borderBottom: '1px solid var(--border)',
            background: 'rgba(255, 255, 255, 0.03)'
          }}>
            {year} Week {week}
          </div>
        </div>
      )}

      {/* Main matchup area - broadcast style */}
      <div style={{ padding: '0.75rem' }}>
        {/* Player Stats - Two Column Layout */}
        {(manager1Players?.length > 0 || manager2Players?.length > 0) && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            gap: '1rem',
            marginTop: '0.25rem'
          }}>
            {/* Manager 1 Stats */}
            <div>
              <Link to={`/manager/${encodeURIComponent(manager1.name)}`} style={{
                textDecoration: 'none',
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '0.5rem'
              }}>
                {manager1.image_url && (
                  <img
                    src={manager1.image_url}
                    alt={manager1.name}
                    style={{
                      width: '100px',
                      height: '100px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '3px solid rgba(255, 255, 255, 0.1)',
                      boxShadow: manager1Won ? '0 0 12px rgba(46, 204, 113, 0.4), 0 0 24px rgba(46, 204, 113, 0.2)' : 'none',
                      opacity: manager1Won ? 1 : 0.8,
                      filter: manager1Won ? 'none' : 'grayscale(0.15)'
                    }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
              </Link>
              {/* Manager 1 Name */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '0.5rem'
              }}>
                <div style={{
                  fontSize: '1rem',
                  fontWeight: 400,
                  color: manager1Won ? 'rgba(46, 204, 113, 1)' : 'var(--muted)',
                  textShadow: manager1Won ? '0 0 8px rgba(46, 204, 113, 0.3), 0 0 15px rgba(46, 204, 113, 0.15)' : 'none'
                }}>
                  {manager1.name}
                </div>
              </div>
              {/* Manager 1 Final Score */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '0.75rem'
              }}>
                <div style={{
                  fontSize: '2.5rem',
                  fontWeight: 400,
                  lineHeight: 1,
                  color: manager1Won ? 'rgba(46, 204, 113, 1)' : 'rgba(255, 255, 255, 0.4)',
                  fontVariantNumeric: 'tabular-nums',
                  letterSpacing: '2px',
                  fontFamily: '"7segment", monospace',
                  textShadow: manager1Won ? '0 0 8px rgba(46, 204, 113, 0.3), 0 0 15px rgba(46, 204, 113, 0.15)' : 'none'
                }}>
                  {manager1Score?.toFixed(2)}
                </div>
              </div>
              {/* All Players */}
              {manager1Players?.map((player, i) => (
                <Link
                  key={i}
                  to={`/player/${player.slug || encodeURIComponent(player.name?.toLowerCase() || '')}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0',
                    fontSize: '0.85rem',
                    color: 'var(--text)',
                    textDecoration: 'none',
                    borderBottom: i < 2 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    borderTop: i === 0 || i === 3 ? '4px solid rgba(255, 255, 255, 0.15)' : 'none',
                    paddingTop: i === 3 ? '0.75rem' : '0.5rem',
                    minHeight: '52px'
                  }}
                >
                  {player.image_url && (
                    <img
                      src={player.image_url}
                      alt={player.name}
                      style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '4px',
                        objectFit: 'cover',
                        flexShrink: 0,
                        opacity: manager1Won ? 1 : 0.8,
                        filter: manager1Won ? 'none' : 'grayscale(0.15)'
                      }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  )}
                  <div style={{
                    flex: 1,
                    textAlign: 'center',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.1rem'
                  }}>
                    {player.first_name && (
                      <div style={{
                        fontWeight: 400,
                        color: 'var(--muted)',
                        fontSize: '0.8rem',
                        opacity: manager1Won ? 1 : 0.6
                      }}>
                        {player.first_name}
                      </div>
                    )}
                    {player.last_name && (
                      <div style={{
                        fontWeight: 600,
                        color: manager1Won ? 'var(--text)' : 'var(--muted)',
                        fontSize: '0.85rem',
                        opacity: manager1Won ? 1 : 0.7
                      }}>
                        {player.last_name}
                      </div>
                    )}
                    {player.position && (
                      <div style={{
                        fontSize: '0.6rem',
                        color: 'var(--muted)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        opacity: manager1Won ? 0.5 : 0.4
                      }}>
                        {player.position}
                      </div>
                    )}
                  </div>
                  <div style={{
                    fontWeight: 400,
                    color: manager1Won ? 'var(--text)' : 'rgba(255, 255, 255, 0.5)',
                    minWidth: '55px',
                    textAlign: 'right',
                    fontSize: '1.5rem',
                    fontVariantNumeric: 'tabular-nums',
                    letterSpacing: '1px',
                    fontFamily: '"7segment", monospace'
                  }}>
                    {player.score?.toFixed(2)}
                  </div>
                </Link>
              ))}
            </div>

            {/* Vertical Divider */}
            <div style={{
              width: '1px',
              background: 'var(--border)',
              height: '100%'
            }} />

            {/* Manager 2 Stats */}
            <div>
              <Link to={`/manager/${encodeURIComponent(manager2.name)}`} style={{
                textDecoration: 'none',
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '0.5rem'
              }}>
                {manager2.image_url && (
                  <img
                    src={manager2.image_url}
                    alt={manager2.name}
                    style={{
                      width: '100px',
                      height: '100px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '3px solid rgba(255, 255, 255, 0.1)',
                      boxShadow: manager2Won ? '0 0 12px rgba(46, 204, 113, 0.4), 0 0 24px rgba(46, 204, 113, 0.2)' : 'none',
                      opacity: manager2Won ? 1 : 0.8,
                      filter: manager2Won ? 'none' : 'grayscale(0.15)'
                    }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
              </Link>
              {/* Manager 2 Name */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '0.5rem'
              }}>
                <div style={{
                  fontSize: '1rem',
                  fontWeight: 400,
                  color: manager2Won ? 'rgba(46, 204, 113, 1)' : 'var(--muted)',
                  textShadow: manager2Won ? '0 0 8px rgba(46, 204, 113, 0.3), 0 0 15px rgba(46, 204, 113, 0.15)' : 'none'
                }}>
                  {manager2.name}
                </div>
              </div>
              {/* Manager 2 Final Score */}
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                marginBottom: '0.75rem'
              }}>
                <div style={{
                  fontSize: '2.5rem',
                  fontWeight: 400,
                  lineHeight: 1,
                  color: manager2Won ? 'rgba(46, 204, 113, 1)' : 'rgba(255, 255, 255, 0.4)',
                  fontVariantNumeric: 'tabular-nums',
                  letterSpacing: '2px',
                  fontFamily: '"7segment", monospace',
                  textShadow: manager2Won ? '0 0 8px rgba(46, 204, 113, 0.3), 0 0 15px rgba(46, 204, 113, 0.15)' : 'none'
                }}>
                  {manager2Score?.toFixed(2)}
                </div>
              </div>
              {/* All Players */}
              {manager2Players?.map((player, i) => (
                <Link
                  key={i}
                  to={`/player/${player.slug || encodeURIComponent(player.name?.toLowerCase() || '')}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0',
                    fontSize: '0.85rem',
                    color: 'var(--text)',
                    textDecoration: 'none',
                    borderBottom: i < 2 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none',
                    borderTop: i === 0 || i === 3 ? '4px solid rgba(255, 255, 255, 0.15)' : 'none',
                    paddingTop: i === 3 ? '0.75rem' : '0.5rem',
                    minHeight: '52px'
                  }}
                >
                  <div style={{
                    fontWeight: 400,
                    color: manager2Won ? 'var(--text)' : 'rgba(255, 255, 255, 0.5)',
                    minWidth: '55px',
                    textAlign: 'left',
                    fontSize: '1.5rem',
                    fontVariantNumeric: 'tabular-nums',
                    letterSpacing: '1px',
                    fontFamily: '"7segment", monospace'
                  }}>
                    {player.score?.toFixed(2)}
                  </div>
                  <div style={{
                    flex: 1,
                    textAlign: 'center',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.1rem'
                  }}>
                    {player.first_name && (
                      <div style={{
                        fontWeight: 400,
                        color: 'var(--muted)',
                        fontSize: '0.8rem',
                        opacity: manager2Won ? 1 : 0.6
                      }}>
                        {player.first_name}
                      </div>
                    )}
                    {player.last_name && (
                      <div style={{
                        fontWeight: 600,
                        color: manager2Won ? 'var(--text)' : 'var(--muted)',
                        fontSize: '0.85rem',
                        opacity: manager2Won ? 1 : 0.7
                      }}>
                        {player.last_name}
                      </div>
                    )}
                    {player.position && (
                      <div style={{
                        fontSize: '0.6rem',
                        color: 'var(--muted)',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        opacity: manager2Won ? 0.5 : 0.4
                      }}>
                        {player.position}
                      </div>
                    )}
                  </div>
                  {player.image_url && (
                    <img
                      src={player.image_url}
                      alt={player.name}
                      style={{
                        width: '42px',
                        height: '42px',
                        borderRadius: '4px',
                        objectFit: 'cover',
                        flexShrink: 0,
                        opacity: manager2Won ? 1 : 0.8,
                        filter: manager2Won ? 'none' : 'grayscale(0.15)'
                      }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  )}
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Margin Info */}
        {showMargin && matchup.differential !== undefined && (
          <div style={{
            marginTop: '1rem',
            paddingTop: '1rem',
            borderTop: '1px solid var(--border)',
            textAlign: 'center',
            fontSize: '0.75rem',
            color: 'var(--muted)',
            fontWeight: 600,
            letterSpacing: '0.5px'
          }}>
            MARGIN: {Math.abs(matchup.differential).toFixed(2)} pts
          </div>
        )}
      </div>
    </div>
  );
}
