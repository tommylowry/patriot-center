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

  const manager1Won = winner === manager1.name;
  const manager2Won = winner === manager2.name;

  return (
    <div style={{
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Header with game info */}
      {!hideHeader && week && year && (
        <div style={{
          padding: '0.75rem 0 0.5rem 0',
          textAlign: 'center',
          fontSize: '0.95rem',
          fontWeight: 700,
          letterSpacing: '1.5px',
          textTransform: 'uppercase',
          color: 'var(--text)',
          marginBottom: '0.75rem'
        }}>
          {year} Week {week}
        </div>
      )}

      {/* Main matchup area - broadcast style */}
      <div style={{ padding: '0.75rem' }}>
        {/* Top Section - Logos, Names and Scores */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          marginBottom: '0.75rem'
        }}>
          {/* Manager 1 Logo */}
          <Link to={`/manager/${encodeURIComponent(manager1.name)}`} style={{ textDecoration: 'none' }}>
            {manager1.image_url && (
              <img
                src={manager1.image_url}
                alt={manager1.name}
                style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: `3px solid ${manager1Won ? 'var(--success)' : 'rgba(255, 255, 255, 0.1)'}`,
                  boxShadow: manager1Won ? '0 0 20px rgba(46, 204, 113, 0.4)' : 'none'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
          </Link>

          {/* Center - Names and Scores (stacked like NHL broadcast) */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {/* Manager 1 Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Link
                to={`/manager/${encodeURIComponent(manager1.name)}`}
                style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                  color: manager1Won ? 'var(--success)' : 'var(--text)',
                  textDecoration: 'none',
                  textShadow: manager1Won ? '0 0 15px rgba(46, 204, 113, 0.3)' : 'none'
                }}
              >
                {manager1.name}
              </Link>
              <div style={{
                fontSize: '1.8rem',
                fontWeight: 900,
                lineHeight: 1,
                color: manager1Won ? 'var(--success)' : 'var(--text)',
                textShadow: manager1Won ? '0 0 20px rgba(46, 204, 113, 0.4)' : 'none',
                fontVariantNumeric: 'tabular-nums'
              }}>
                {manager1Score?.toFixed(2)}
              </div>
            </div>

            {/* Manager 2 Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Link
                to={`/manager/${encodeURIComponent(manager2.name)}`}
                style={{
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                  color: manager2Won ? 'var(--success)' : 'var(--text)',
                  textDecoration: 'none',
                  textShadow: manager2Won ? '0 0 15px rgba(46, 204, 113, 0.3)' : 'none'
                }}
              >
                {manager2.name}
              </Link>
              <div style={{
                fontSize: '1.8rem',
                fontWeight: 900,
                lineHeight: 1,
                color: manager2Won ? 'var(--success)' : 'var(--text)',
                textShadow: manager2Won ? '0 0 20px rgba(46, 204, 113, 0.4)' : 'none',
                fontVariantNumeric: 'tabular-nums'
              }}>
                {manager2Score?.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Manager 2 Logo */}
          <Link to={`/manager/${encodeURIComponent(manager2.name)}`} style={{ textDecoration: 'none' }}>
            {manager2.image_url && (
              <img
                src={manager2.image_url}
                alt={manager2.name}
                style={{
                  width: '60px',
                  height: '60px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: `3px solid ${manager2Won ? 'var(--success)' : 'rgba(255, 255, 255, 0.1)'}`,
                  boxShadow: manager2Won ? '0 0 20px rgba(46, 204, 113, 0.4)' : 'none'
                }}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            )}
          </Link>
        </div>

        {/* Divider Bar */}
        <div style={{
          height: '1px',
          background: 'var(--border)',
          margin: '0.5rem 0'
        }} />

        {/* Player Stats - Two Column Layout */}
        {(manager1TopScorers?.length > 0 || manager2TopScorers?.length > 0) && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr',
            gap: '1rem'
          }}>
            {/* Manager 1 Stats */}
            <div>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                letterSpacing: '1px',
                textTransform: 'uppercase',
                color: 'var(--muted)',
                marginBottom: '0.75rem',
                paddingBottom: '0.5rem',
                borderBottom: '1px solid var(--border)'
              }}>
                {manager1.name}
              </div>
              {manager1TopScorers?.slice(0, 3).map((player, i) => (
                <Link
                  key={i}
                  to={`/player/${player.slug || encodeURIComponent(player.name.toLowerCase())}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0',
                    fontSize: '0.85rem',
                    color: 'var(--text)',
                    textDecoration: 'none',
                    borderBottom: i < 2 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none'
                  }}
                >
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
                  <div style={{
                    fontWeight: 600,
                    flex: 1,
                    color: 'var(--text)',
                    textAlign: 'left'
                  }}>
                    {player.name}
                  </div>
                  <div style={{
                    fontWeight: 700,
                    color: 'var(--accent)',
                    minWidth: '45px',
                    textAlign: 'right'
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
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                letterSpacing: '1px',
                textTransform: 'uppercase',
                color: 'var(--muted)',
                marginBottom: '0.75rem',
                paddingBottom: '0.5rem',
                borderBottom: '1px solid var(--border)'
              }}>
                {manager2.name}
              </div>
              {manager2TopScorers?.slice(0, 3).map((player, i) => (
                <Link
                  key={i}
                  to={`/player/${player.slug || encodeURIComponent(player.name.toLowerCase())}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0',
                    fontSize: '0.85rem',
                    color: 'var(--text)',
                    textDecoration: 'none',
                    borderBottom: i < 2 ? '1px solid rgba(255, 255, 255, 0.05)' : 'none'
                  }}
                >
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
                  <div style={{
                    fontWeight: 600,
                    flex: 1,
                    color: 'var(--text)',
                    textAlign: 'left'
                  }}>
                    {player.name}
                  </div>
                  <div style={{
                    fontWeight: 700,
                    color: 'var(--accent)',
                    minWidth: '45px',
                    textAlign: 'right'
                  }}>
                    {player.score?.toFixed(2)}
                  </div>
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
