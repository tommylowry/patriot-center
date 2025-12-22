import React from 'react';
import { Link } from 'react-router-dom';

/**
 * TradeCard - Visual trade card with team logos and player headshots
 * Emphasis on received players with images, sent players as simple text
 */
export function TradeCard({ trade }) {
  if (!trade) return null;

  const managersInvolved = trade.managers_involved || [];
  const week = trade.week;
  const year = trade.year;

  return (
    <div style={{
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      {/* Header */}
      {week && year && (
        <div style={{
          background: 'var(--bg-alt)',
          padding: '0.5rem 1rem',
          textAlign: 'center',
          fontSize: '0.7rem',
          fontWeight: 700,
          letterSpacing: '1.5px',
          textTransform: 'uppercase',
          color: 'var(--muted)',
          borderBottom: '1px solid var(--border)'
        }}>
          Week {week} {year}
        </div>
      )}

      {/* Trade Content */}
      <div style={{ padding: '1.5rem' }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${managersInvolved.length}, 1fr)`,
          gap: '2rem'
        }}>
          {managersInvolved.map((manager, idx) => {
            const managerName = typeof manager === 'string' ? manager : manager?.name || 'Unknown';
            const managerImageUrl = typeof manager === 'object' ? manager?.image_url : null;
            const managerKey = managerName.toLowerCase().replace(/\s+/g, '_');
            const received = trade[`${managerKey}_received`] || [];
            const sent = trade[`${managerKey}_sent`] || [];

            return (
              <div key={idx} style={{ textAlign: 'center' }}>
                {/* Team Logo/Avatar at Top */}
                <Link
                  to={`/manager/${encodeURIComponent(managerName)}`}
                  style={{ textDecoration: 'none', display: 'inline-block', marginBottom: '1rem' }}
                >
                  {managerImageUrl && (
                    <div style={{
                      width: '70px',
                      height: '70px',
                      margin: '0 auto 0.75rem',
                      position: 'relative'
                    }}>
                      <img
                        src={managerImageUrl}
                        alt={managerName}
                        style={{
                          width: '100%',
                          height: '100%',
                          borderRadius: '50%',
                          objectFit: 'cover',
                          border: '2px solid var(--border)'
                        }}
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <div style={{
                    fontSize: '1rem',
                    fontWeight: 700,
                    color: 'var(--text)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {managerName}
                  </div>
                </Link>

                {/* Received Players - Emphasized with headshots flowing together */}
                {received.length > 0 && (
                  <div style={{ marginBottom: '1.5rem' }}>
                    <div style={{
                      fontSize: '0.65rem',
                      color: 'var(--success)',
                      marginBottom: '0.75rem',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '1px'
                    }}>
                      Received
                    </div>

                    {/* Player Images Row - flowing together without borders */}
                    <div style={{
                      display: 'flex',
                      gap: '0.25rem',
                      justifyContent: 'center',
                      marginBottom: '0.5rem',
                      flexWrap: 'wrap'
                    }}>
                      {received.map((player, i) => {
                        const playerName = player.name || 'Unknown';
                        const playerSlug = player.slug || encodeURIComponent(playerName.toLowerCase());
                        const isFAAB = playerName.includes('FAAB');

                        if (isFAAB) {
                          return (
                            <div key={i}>
                              {player.image_url && (
                                <img
                                  src={player.image_url}
                                  alt={playerName}
                                  style={{
                                    width: '55px',
                                    height: '55px',
                                    borderRadius: '6px',
                                    objectFit: 'cover'
                                  }}
                                  onError={(e) => {
                                    e.target.style.display = 'none';
                                  }}
                                />
                              )}
                            </div>
                          );
                        }

                        return (
                          <Link
                            key={i}
                            to={`/player/${playerSlug}`}
                            style={{ textDecoration: 'none' }}
                          >
                            {player.image_url && (
                              <img
                                src={player.image_url}
                                alt={playerName}
                                style={{
                                  width: '55px',
                                  height: '55px',
                                  borderRadius: '6px',
                                  objectFit: 'cover'
                                }}
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                }}
                              />
                            )}
                          </Link>
                        );
                      })}
                    </div>

                    {/* Player Names */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                      {received.map((player, i) => {
                        const playerName = player.name || 'Unknown';
                        const playerSlug = player.slug || encodeURIComponent(playerName.toLowerCase());
                        const isFAAB = playerName.includes('FAAB');

                        return (
                          <div key={i} style={{ fontSize: '0.75rem' }}>
                            {isFAAB ? (
                              <span style={{
                                color: 'var(--text)',
                                fontWeight: 600
                              }}>
                                {playerName}
                              </span>
                            ) : (
                              <Link
                                to={`/player/${playerSlug}`}
                                style={{
                                  color: 'var(--accent)',
                                  textDecoration: 'none',
                                  fontWeight: 600
                                }}
                              >
                                {playerName}
                              </Link>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Sent Players - Just text, no images */}
                {sent.length > 0 && (
                  <div style={{ opacity: 0.4 }}>
                    <div style={{
                      fontSize: '0.6rem',
                      color: 'var(--muted)',
                      marginBottom: '0.5rem',
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>
                      Sent
                    </div>

                    {/* Player Names Only */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
                      {sent.map((player, i) => {
                        const playerName = player.name || 'Unknown';
                        const playerSlug = player.slug || encodeURIComponent(playerName.toLowerCase());
                        const isFAAB = playerName.includes('FAAB');

                        return (
                          <div key={i} style={{ fontSize: '0.65rem' }}>
                            {isFAAB ? (
                              <span style={{
                                color: 'var(--muted)',
                                fontWeight: 500
                              }}>
                                {playerName}
                              </span>
                            ) : (
                              <Link
                                to={`/player/${playerSlug}`}
                                style={{
                                  color: 'var(--muted)',
                                  textDecoration: 'none',
                                  fontWeight: 500
                                }}
                              >
                                {playerName}
                              </Link>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
