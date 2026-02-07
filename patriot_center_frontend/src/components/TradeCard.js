import React from 'react';
import { Link } from 'react-router-dom';

/**
 * TradeCard - Visual trade card showing player movement between managers
 * Layout: All managers on left/right with connecting arrows to player batches
 */
export function TradeCard({ trade, hideHeader = false, isMobile = false }) {
  if (!trade) return null;

  const managersInvolved = trade.managers_involved || [];
  const week = trade.week;
  const year = trade.year;

  // Check if this is a simple 2-manager trade
  const isSimpleTrade = managersInvolved.length === 2;

  // Simple 2-manager trade layout
  if (isSimpleTrade) {
    // Build movement groups for 2-manager trades
    const playerMovements = [];

    managersInvolved.forEach(manager => {
      const managerName = typeof manager === 'string' ? manager : manager?.name || 'Unknown';
      const managerImageUrl = typeof manager === 'object' ? manager?.image_url : null;
      const managerKey = managerName.toLowerCase().replace(/\s+/g, '_');
      const received = trade[`${managerKey}_received`] || [];

      received.forEach(player => {
        let receivingManager = null;
        let receivingManagerImage = null;

        for (const otherManager of managersInvolved) {
          const otherName = typeof otherManager === 'string' ? otherManager : otherManager?.name || 'Unknown';
          if (otherName === managerName) continue;

          const otherKey = otherName.toLowerCase().replace(/\s+/g, '_');
          const otherReceived = trade[`${otherKey}_received`] || [];

          if (otherReceived.some(p => p.name === player.name)) {
            receivingManager = otherName;
            receivingManagerImage = typeof otherManager === 'object' ? otherManager?.image_url : null;
            break;
          }
        }

        playerMovements.push({
          player,
          fromManager: managerName,
          fromManagerImage: managerImageUrl,
          toManager: receivingManager || 'Unknown',
          toManagerImage: receivingManagerImage
        });
      });
    });

    const groupedMovements = {};
    playerMovements.forEach(movement => {
      const key = `${movement.fromManager}→${movement.toManager}`;
      if (!groupedMovements[key]) {
        groupedMovements[key] = {
          fromManager: movement.fromManager,
          fromManagerImage: movement.fromManagerImage,
          toManager: movement.toManager,
          toManagerImage: movement.toManagerImage,
          players: []
        };
      }
      groupedMovements[key].players.push(movement.player);
    });

    const movementGroups = Object.values(groupedMovements);

    return (
      <div style={{
        borderRadius: '8px',
        overflow: 'hidden',
        border: '1px solid var(--border)',
        maxWidth: '1200px',
        width: '100%'
      }}>
        {/* Header */}
        {!hideHeader && week && year && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            marginBottom: isMobile ? '0.25rem' : '0.5rem'
          }}>
            <div style={{
              padding: isMobile ? '0.4rem 0.75rem 0.3rem 0.75rem' : '0.6rem 1rem 0.4rem 1rem',
              fontSize: isMobile ? '0.75rem' : '1rem',
              fontWeight: 700,
              letterSpacing: isMobile ? '1px' : '1.5px',
              textTransform: 'uppercase',
              color: 'var(--text)',
              borderLeft: '1px solid var(--border)',
              borderRight: '1px solid var(--border)',
              borderBottom: '1px solid var(--border)',
              background: 'rgba(255, 255, 255, 0.03)'
            }}>
              {year} Week {week}
            </div>
            <div style={{
              fontSize: isMobile ? '0.55rem' : '0.65rem',
              color: 'var(--muted)',
              marginTop: isMobile ? '0.35rem' : '0.5rem',
              fontStyle: 'italic'
            }}>
              Post trade calculations coming soon!
            </div>
          </div>
        )}

        {/* Trade Content */}
        <div style={{ padding: isMobile ? '0.75rem' : '1.5rem' }}>
          {(() => {
            // Calculate sizing ONCE for the entire trade to ensure consistency across all managers
            const allPlayers = movementGroups.flatMap(g => g.players);
            const maxPlayerCount = Math.max(...movementGroups.map(g => g.players.length), 1);
            // On mobile with grid layout (>3 players), cap sizing at 3 players per row since grid wraps
            const effectiveMaxPlayerCount = (isMobile && maxPlayerCount > 3) ? 3 : maxPlayerCount;
            const maxLastNameLength = Math.max(
              ...allPlayers.map(p => (p.last_name || '').length),
              1
            );

            // Base sizes - smaller on mobile
            const basePlayerImageSize = isMobile ? 45 : 70;
            const baseManagerImageSize = isMobile ? 45 : 70;
            const baseFontSize = isMobile ? 0.65 : 0.85;

            // Manager image shrinks based on the MAXIMUM player count across all groups
            const dynamicManagerImageSize = Math.max(isMobile ? 30 : 35, baseManagerImageSize - (effectiveMaxPlayerCount - 1) * (isMobile ? 8 : 12));
            const managerColumnWidth = dynamicManagerImageSize + (isMobile ? 15 : 25);

            // Calculate available width for players
            const totalCardWidth = isMobile ? 375 : 1200; // Typical mobile width
            const padding = isMobile ? 24 : 48;
            const availablePlayerWidth = totalCardWidth - managerColumnWidth - padding;
            const gapSpace = Math.max(0, (effectiveMaxPlayerCount - 1) * (isMobile ? 6 : 10));
            const availablePerPlayer = (availablePlayerWidth - gapSpace) / effectiveMaxPlayerCount;

            // Dynamic player image size
            const dynamicPlayerImageSize = Math.min(basePlayerImageSize, Math.max(isMobile ? 28 : 35, availablePerPlayer * 0.40));

            // Dynamic font size based on LONGEST name across ALL players
            const textWidthPerPlayer = availablePerPlayer - dynamicPlayerImageSize - 8;
            const nameScaleFactor = 8 / maxLastNameLength;
            const referenceTextWidth = 120;
            const spaceScaleFactor = textWidthPerPlayer / referenceTextWidth;

            const minFontSize = isMobile ? 0.45 : 0.55;
            const maxFontSize = isMobile ? 0.9 : 1.2;
            const calculatedFontSize = baseFontSize * nameScaleFactor * spaceScaleFactor;
            const dynamicFontSize = Math.max(minFontSize, Math.min(maxFontSize, calculatedFontSize));

            // Minimize vertical spacing between trade directions
            const verticalGap = isMobile ? 0.5 : 0.75;

            // Calculate manager name font size separately to ensure manager names always fit
            // Get longest manager name
            const allManagerNames = movementGroups.flatMap(g => [g.fromManager, g.toManager]);
            const maxManagerNameLength = Math.max(
              ...allManagerNames.map(name => (name || '').length),
              1
            );

            // Available width for manager name accounting for ALL padding and borders
            // managerColumnWidth includes base column, but Link has paddingRight: 1.5rem (24px)
            // Also account for border (1px) and some breathing room
            const managerNameWidth = managerColumnWidth - 40; // 24px padding + 16px for safety

            // Calculate font size that fits the longest manager name on ONE line
            // Using a more conservative character width estimate (0.7em per character)
            // Formula: available_width / (characters * char_width_multiplier)
            const calculatedManagerFontSize = managerNameWidth / (maxManagerNameLength * 0.7 * 16);

            const managerNameFontSize = Math.min(
              isMobile ? 0.65 : 0.85, // Max size for aesthetics
              Math.max(
                isMobile ? 0.4 : 0.45, // Min size for readability - lower to handle extreme cases
                calculatedManagerFontSize
              )
            );

            return (
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                gap: `${verticalGap}rem`
              }}>
                {movementGroups.map((group, idx) => {
                  return (
                    <div key={idx} style={{
                  display: 'grid',
                  gridTemplateColumns: `${managerColumnWidth}px 1fr`,
                  alignItems: 'center',
                  borderBottom: idx < movementGroups.length - 1 ? '1px solid var(--border)' : 'none',
                  paddingBottom: idx < movementGroups.length - 1 ? `${verticalGap}rem` : '0',
                  paddingTop: idx > 0 ? `${verticalGap}rem` : '0'
                }}>
                  {/* Left: Sending Manager */}
                  <Link
                    to={`/manager/${encodeURIComponent(group.fromManager)}`}
                    style={{
                      textDecoration: 'none',
                      display: 'inline-flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: isMobile ? '0.25rem' : '0.5rem',
                      border: '1px solid transparent',
                      background: 'transparent',
                      borderRadius: '8px',
                      transition: 'all 0.2s ease',
                      cursor: 'pointer',
                      boxSizing: 'border-box'
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
                    {group.fromManagerImage && (
                      <img
                        src={group.fromManagerImage}
                        alt={group.fromManager}
                        style={{
                          width: `${dynamicManagerImageSize}px`,
                          height: `${dynamicManagerImageSize}px`,
                          borderRadius: '50%',
                          objectFit: 'cover'
                        }}
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    )}
                    <div style={{
                      fontSize: `${managerNameFontSize}rem`,
                      fontWeight: 600,
                      color: 'var(--text)',
                      textAlign: 'center',
                      width: '100%',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {group.fromManager}
                    </div>
                  </Link>

                  {/* Right: Players batch */}
                  <div style={{
                    display: isMobile && group.players.length > 3 ? 'grid' : 'flex',
                    gridTemplateColumns: isMobile && group.players.length > 3 ? 'repeat(3, 1fr)' : undefined,
                    gap: isMobile ? '0.4rem' : '0.75rem',
                    justifyContent: isMobile && group.players.length > 3 ? undefined : 'space-evenly',
                    alignItems: isMobile && group.players.length > 3 ? undefined : 'center',
                    flexWrap: isMobile && group.players.length > 3 ? undefined : 'nowrap',
                    paddingLeft: isMobile ? '0.5rem' : '1.5rem',
                    borderLeft: '1px solid var(--border)',
                    overflow: 'hidden'
                  }}>
                    {group.players.map((player, playerIdx) => {
                      const playerName = player.name || 'Unknown';
                      const playerId = player?.player_id;
                      const isFAAB = playerName.includes('FAAB') || player?.provide_link === false;
                      const remainder = isMobile && group.players.length > 3 ? group.players.length % 3 : 0;
                      const isLastAndSingle = remainder === 1 && playerIdx === group.players.length - 1;
                      const isFirstOfTwoLeftover = remainder === 2 && playerIdx === group.players.length - 2;
                      const isSecondOfTwoLeftover = remainder === 2 && playerIdx === group.players.length - 1;

                      // For 2 leftovers, create a wrapper for both players
                      if (isFirstOfTwoLeftover) {
                        const leftoverPlayers = [player, group.players[playerIdx + 1]];
                        return (
                          <div key={`wrapper-${playerIdx}`} style={{
                            gridColumn: '1 / -1',
                            display: 'flex',
                            justifyContent: 'space-evenly',
                            alignItems: 'center',
                            flexWrap: 'nowrap',
                            gap: isMobile ? '0.4rem' : '0.75rem'
                          }}>
                            {leftoverPlayers.map((p, idx) => {
                              const pName = p.name || 'Unknown';
                              const pId = p?.player_id;
                              const pIsFAAB = pName.includes('FAAB') || p?.provide_link === false;

                              return (
                                <div key={playerIdx + idx} style={{
                                  display: 'flex',
                                  flexDirection: 'column',
                                  alignItems: 'center',
                                  gap: isMobile ? '0.25rem' : '0.5rem',
                                  flex: '1 1 0',
                                  minWidth: 0
                                }}>
                                  {pIsFAAB ? (
                                    <>
                                      {p.image_url && (
                                        <img
                                          src={p.image_url}
                                          alt={pName}
                                          style={{
                                            width: `${dynamicPlayerImageSize}px`,
                                            height: `${dynamicPlayerImageSize}px`,
                                            borderRadius: '8px',
                                            objectFit: 'cover'
                                          }}
                                          onError={(e) => {
                                            e.target.style.display = 'none';
                                          }}
                                        />
                                      )}
                                      <div style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: '0.1rem',
                                        width: '100%'
                                      }}>
                                        {p.first_name && (
                                          <div style={{
                                            fontSize: `${dynamicFontSize * 0.9}rem`,
                                            fontWeight: 400,
                                            color: 'var(--muted)',
                                            textAlign: 'center',
                                            width: '100%',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                          }}>
                                            {p.first_name}
                                          </div>
                                        )}
                                        {p.last_name && (
                                          <div style={{
                                            fontSize: `${dynamicFontSize}rem`,
                                            fontWeight: 600,
                                            color: 'var(--text)',
                                            textAlign: 'center',
                                            width: '100%',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                          }}>
                                            {p.last_name}
                                          </div>
                                        )}
                                      </div>
                                    </>
                                  ) : (
                                    <Link
                                      to={`/player/${pId}`}
                                      style={{
                                        textDecoration: 'none',
                                        display: 'inline-flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: isMobile ? '0.25rem' : '0.5rem',
                                        border: '1px solid transparent',
                                        background: 'transparent',
                                        borderRadius: '8px',
                                        transition: 'all 0.2s ease',
                                        cursor: 'pointer',
                                        boxSizing: 'border-box'
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
                                      {p.image_url && (
                                        <img
                                          src={p.image_url}
                                          alt={pName}
                                          style={{
                                            width: `${dynamicPlayerImageSize}px`,
                                            height: `${dynamicPlayerImageSize}px`,
                                            borderRadius: '8px',
                                            objectFit: 'cover'
                                          }}
                                          onError={(e) => {
                                            e.target.style.display = 'none';
                                          }}
                                        />
                                      )}
                                      <div style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        alignItems: 'center',
                                        gap: '0.1rem',
                                        width: '100%'
                                      }}>
                                        {p.first_name && (
                                          <div style={{
                                            fontSize: `${dynamicFontSize * 0.9}rem`,
                                            fontWeight: 400,
                                            color: 'var(--muted)',
                                            textAlign: 'center',
                                            width: '100%',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                          }}>
                                            {p.first_name}
                                          </div>
                                        )}
                                        {p.last_name && (
                                          <div style={{
                                            fontSize: `${dynamicFontSize}rem`,
                                            fontWeight: 600,
                                            color: 'var(--accent)',
                                            textAlign: 'center',
                                            width: '100%',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                          }}>
                                            {p.last_name}
                                          </div>
                                        )}
                                      </div>
                                    </Link>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        );
                      }

                      // Skip the second player of a 2-leftover pair as it's rendered in the wrapper
                      if (isSecondOfTwoLeftover) {
                        return null;
                      }

                      return (
                        <div key={playerIdx} style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: isMobile ? '0.25rem' : '0.5rem',
                          flex: (isMobile && group.players.length > 3) ? undefined : '1 1 0',
                          minWidth: 0,
                          gridColumn: isLastAndSingle ? '1 / -1' : undefined,
                          justifySelf: isLastAndSingle ? 'center' : undefined,
                          maxWidth: isLastAndSingle ? '33%' : undefined
                        }}>
                          {isFAAB ? (
                            <>
                              {player.image_url && (
                                <img
                                  src={player.image_url}
                                  alt={playerName}
                                  style={{
                                    width: `${dynamicPlayerImageSize}px`,
                                    height: `${dynamicPlayerImageSize}px`,
                                    borderRadius: '8px',
                                    objectFit: 'cover'
                                  }}
                                  onError={(e) => {
                                    e.target.style.display = 'none';
                                  }}
                                />
                              )}
                              <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.1rem',
                                width: '100%'
                              }}>
                                {player.first_name && (
                                  <div style={{
                                    fontSize: `${dynamicFontSize * 0.9}rem`,
                                    fontWeight: 400,
                                    color: 'var(--muted)',
                                    textAlign: 'center',
                                    width: '100%',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {player.first_name}
                                  </div>
                                )}
                                {player.last_name && (
                                  <div style={{
                                    fontSize: `${dynamicFontSize}rem`,
                                    fontWeight: 600,
                                    color: 'var(--text)',
                                    textAlign: 'center',
                                    width: '100%',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {player.last_name}
                                  </div>
                                )}
                              </div>
                            </>
                          ) : (
                            <Link
                              to={`/player/${playerId}`}
                              style={{
                                textDecoration: 'none',
                                display: 'inline-flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: isMobile ? '0.25rem' : '0.5rem',
                                border: '1px solid transparent',
                                background: 'transparent',
                                borderRadius: '8px',
                                transition: 'all 0.2s ease',
                                cursor: 'pointer',
                                boxSizing: 'border-box'
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
                              {player.image_url && (
                                <img
                                  src={player.image_url}
                                  alt={playerName}
                                  style={{
                                    width: `${dynamicPlayerImageSize}px`,
                                    height: `${dynamicPlayerImageSize}px`,
                                    borderRadius: '8px',
                                    objectFit: 'cover'
                                  }}
                                  onError={(e) => {
                                    e.target.style.display = 'none';
                                  }}
                                />
                              )}
                              <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                gap: '0.1rem',
                                width: '100%'
                              }}>
                                {player.first_name && (
                                  <div style={{
                                    fontSize: `${dynamicFontSize * 0.9}rem`,
                                    fontWeight: 400,
                                    color: 'var(--muted)',
                                    textAlign: 'center',
                                    width: '100%',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {player.first_name}
                                  </div>
                                )}
                                {player.last_name && (
                                  <div style={{
                                    fontSize: `${dynamicFontSize}rem`,
                                    fontWeight: 600,
                                    color: 'var(--accent)',
                                    textAlign: 'center',
                                    width: '100%',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}>
                                    {player.last_name}
                                  </div>
                                )}
                              </div>
                            </Link>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
                  );
                })}
              </div>
            );
          })()}
        </div>
      </div>
    );
  }

  // Complex multi-manager trade layout - Table format
  // Build manager rows: each manager with what they sent and received
  const managerRows = managersInvolved.map(manager => {
    const managerName = typeof manager === 'string' ? manager : manager?.name || 'Unknown';
    const managerImageUrl = typeof manager === 'object' ? manager?.image_url : null;
    const managerKey = managerName.toLowerCase().replace(/\s+/g, '_');

    const sent = trade[`${managerKey}_sent`] || [];
    const received = trade[`${managerKey}_received`] || [];

    return {
      name: managerName,
      imageUrl: managerImageUrl,
      sent,
      received
    };
  });

  // Calculate dynamic sizing based on max players in each column
  const maxSentCount = Math.max(...managerRows.map(row => row.sent.length), 1);
  const maxReceivedCount = Math.max(...managerRows.map(row => row.received.length), 1);

  // Calculate sizing for sent column (smaller - 1fr) - reduced on mobile
  const sentBaseImageSize = isMobile ? 40 : 60;
  const sentBaseFontSize = isMobile ? 0.6 : 0.75;
  const sentImageSize = Math.max(isMobile ? 28 : 35, sentBaseImageSize - (maxSentCount - 1) * (isMobile ? 6 : 8));
  const sentFirstNameSize = Math.max(isMobile ? 0.4 : 0.5, sentBaseFontSize * 0.85 - (maxSentCount - 1) * 0.04);
  const sentLastNameSize = Math.max(isMobile ? 0.5 : 0.6, sentBaseFontSize - (maxSentCount - 1) * 0.04);

  // Calculate sizing for received column (larger - 2fr) - reduced on mobile
  // Received players should stay large to be the "star of the show"
  const receivedBaseImageSize = isMobile ? 55 : 80;
  const receivedBaseFontSize = isMobile ? 0.7 : 0.9;
  // Only shrink slightly for extreme cases (5+ players)
  const receivedImageSize = Math.max(isMobile ? 45 : 65, receivedBaseImageSize - (maxReceivedCount - 1) * 2);
  const receivedFirstNameSize = Math.max(isMobile ? 0.6 : 0.75, receivedBaseFontSize * 0.85 - (maxReceivedCount - 1) * 0.01);
  const receivedLastNameSize = Math.max(isMobile ? 0.65 : 0.85, receivedBaseFontSize - (maxReceivedCount - 1) * 0.01);

  return (
    <div style={{
      borderRadius: '8px',
      overflow: 'hidden',
      border: '1px solid var(--border)',
      maxWidth: '100%',
      width: '100%'
    }}>
      {/* Header */}
      {!hideHeader && week && year && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          marginBottom: isMobile ? '0.25rem' : '0.5rem'
        }}>
          <div style={{
            padding: isMobile ? '0.5rem 1rem 0.4rem 1rem' : '0.75rem 1.5rem 0.5rem 1.5rem',
            fontSize: isMobile ? '0.85rem' : '1.15rem',
            fontWeight: 700,
            letterSpacing: isMobile ? '1px' : '1.5px',
            textTransform: 'uppercase',
            color: 'var(--text)',
            borderLeft: '1px solid var(--border)',
            borderRight: '1px solid var(--border)',
            borderBottom: '1px solid var(--border)',
            background: 'rgba(255, 255, 255, 0.03)'
          }}>
            {year} Week {week}
          </div>
          {!isMobile && (
            <div style={{
              fontSize: '0.65rem',
              color: 'var(--muted)',
              marginTop: '0.5rem',
              fontStyle: 'italic'
            }}>
              Post trade calculations coming soon!
            </div>
          )}
        </div>
      )}

      {/* Trade Content - Table Format */}
      <div style={{ padding: isMobile ? '0.75rem' : '1.5rem' }}>
        {/* Header Row */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? '65px 1fr 2fr' : '120px 1fr 2fr',
          borderBottom: '1px solid var(--border)',
          paddingBottom: isMobile ? '0.5rem' : '0.75rem',
          marginBottom: isMobile ? '0.75rem' : '1rem'
        }}>
          <div></div>
          <div style={{
            fontSize: isMobile ? '0.7rem' : '1.3rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: isMobile ? '1px' : '2px',
            color: 'var(--muted)',
            textAlign: 'center',
            borderLeft: '1px solid var(--border)',
            paddingLeft: isMobile ? '0.5rem' : '1rem'
          }}>
            Sent
          </div>
          <div style={{
            fontSize: isMobile ? '0.7rem' : '1.3rem',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: isMobile ? '1px' : '2px',
            color: 'var(--text)',
            textAlign: 'center',
            borderLeft: '1px solid var(--border)',
            paddingLeft: isMobile ? '0.5rem' : '1rem'
          }}>
            Received
          </div>
        </div>

        {/* Manager Rows */}
        {managerRows.map((row, idx) => (
          <div
            key={idx}
            style={{
              display: 'grid',
              gridTemplateColumns: isMobile ? '65px 1fr 2fr' : '120px 1fr 2fr',
              borderBottom: idx < managerRows.length - 1 ? '1px solid var(--border)' : 'none',
              paddingBottom: isMobile ? '0.75rem' : '1.5rem',
              paddingTop: idx > 0 ? (isMobile ? '0.75rem' : '1.5rem') : '0',
              alignItems: 'stretch'
            }}
          >
            {/* Manager Column */}
            <Link
              to={`/manager/${encodeURIComponent(row.name)}`}
              style={{
                textDecoration: 'none',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: isMobile ? '0.25rem' : '0.5rem',
                border: '1px solid transparent',
                background: 'transparent',
                borderRadius: '8px',
                transition: 'all 0.2s ease',
                cursor: 'pointer',
                boxSizing: 'border-box'
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
              {row.imageUrl && (
                <img
                  src={row.imageUrl}
                  alt={row.name}
                  style={{
                    width: isMobile ? '55px' : '85px',
                    height: isMobile ? '55px' : '85px',
                    borderRadius: '50%',
                    objectFit: 'cover'
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
              <div style={{
                fontSize: isMobile ? '0.5rem' : '0.85rem',
                fontWeight: 600,
                color: 'var(--text)',
                textAlign: 'center',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '100%'
              }}>
                {row.name}
              </div>
            </Link>

            {/* Sent Column - De-emphasized (afterthoughts) */}
            <div style={{
              display: isMobile ? 'grid' : 'flex',
              gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : undefined,
              gap: isMobile ? '0.5rem' : '0.5rem',
              flexWrap: isMobile ? undefined : 'nowrap',
              justifyContent: isMobile ? undefined : 'center',
              alignContent: isMobile ? 'center' : undefined,
              alignItems: isMobile ? undefined : 'center',
              borderLeft: '1px solid var(--border)',
              paddingLeft: isMobile ? '0.5rem' : '1rem',
              overflow: 'hidden'
            }}>
              {row.sent.map((player, playerIdx) => {
                const playerName = player.name || 'Unknown';
                const playerId = player?.player_id;
                const isFAAB = playerName.includes('FAAB') || player?.provide_link === false;
                const isLastAndOdd = isMobile && playerIdx === row.sent.length - 1 && row.sent.length % 2 === 1;

                return (
                  <div key={playerIdx} style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.5rem',
                    flex: isMobile ? undefined : '1 1 0',
                    minWidth: 0,
                    gridColumn: isLastAndOdd ? '1 / -1' : undefined,
                    justifySelf: isLastAndOdd ? 'center' : undefined
                  }}>
                    {isFAAB ? (
                      <>
                        {player.image_url && (
                          <img
                            src={player.image_url}
                            alt={playerName}
                            style={{
                              width: `${sentImageSize}px`,
                              height: `${sentImageSize}px`,
                              borderRadius: '8px',
                              objectFit: 'cover',
                              opacity: 0.4,
                              filter: 'grayscale(0.5)'
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        )}
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.1rem',
                          opacity: 0.5,
                          width: '100%'
                        }}>
                          {player.first_name && (
                            <div style={{
                              fontSize: `${sentFirstNameSize}rem`,
                              fontWeight: 400,
                              color: 'var(--muted)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.first_name}
                            </div>
                          )}
                          {player.last_name && (
                            <div style={{
                              fontSize: `${sentLastNameSize}rem`,
                              fontWeight: 600,
                              color: 'var(--muted)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.last_name}
                            </div>
                          )}
                        </div>
                      </>
                    ) : (
                      <Link
                        to={`/player/${playerId}`}
                        style={{
                          textDecoration: 'none',
                          display: 'inline-flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.5rem',
                          border: '1px solid transparent',
                          background: 'transparent',
                          borderRadius: '8px',
                          transition: 'all 0.2s ease',
                          cursor: 'pointer',
                          boxSizing: 'border-box'
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
                        {player.image_url && (
                          <img
                            src={player.image_url}
                            alt={playerName}
                            style={{
                              width: `${sentImageSize}px`,
                              height: `${sentImageSize}px`,
                              borderRadius: '8px',
                              objectFit: 'cover',
                              opacity: 0.4,
                              filter: 'grayscale(0.5)'
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        )}
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.1rem',
                          opacity: 0.5,
                          width: '100%'
                        }}>
                          {player.first_name && (
                            <div style={{
                              fontSize: `${sentFirstNameSize}rem`,
                              fontWeight: 400,
                              color: 'var(--muted)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.first_name}
                            </div>
                          )}
                          {player.last_name && (
                            <div style={{
                              fontSize: `${sentLastNameSize}rem`,
                              fontWeight: 600,
                              color: 'var(--muted)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.last_name}
                            </div>
                          )}
                        </div>
                      </Link>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Received Column */}
            <div style={{
              display: isMobile ? 'grid' : 'flex',
              gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : undefined,
              gap: isMobile ? '0.5rem' : '0.75rem',
              flexWrap: isMobile ? undefined : 'nowrap',
              justifyContent: isMobile ? undefined : 'center',
              alignContent: isMobile ? 'center' : undefined,
              alignItems: isMobile ? undefined : 'center',
              borderLeft: '1px solid var(--border)',
              paddingLeft: isMobile ? '0.5rem' : '1rem',
              overflow: 'hidden'
            }}>
              {row.received.map((player, playerIdx) => {
                const playerName = player.name || 'Unknown';
                const playerId = player?.player_id;
                const isFAAB = playerName.includes('FAAB') || player?.provide_link === false;
                const isLastAndOdd = isMobile && playerIdx === row.received.length - 1 && row.received.length % 2 === 1;

                return (
                  <div key={playerIdx} style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.5rem',
                    flex: isMobile ? undefined : '1 1 0',
                    minWidth: 0,
                    gridColumn: isLastAndOdd ? '1 / -1' : undefined,
                    justifySelf: isLastAndOdd ? 'center' : undefined
                  }}>
                    {isFAAB ? (
                      <>
                        {player.image_url && (
                          <img
                            src={player.image_url}
                            alt={playerName}
                            style={{
                              width: `${receivedImageSize}px`,
                              height: `${receivedImageSize}px`,
                              borderRadius: '8px',
                              objectFit: 'cover'
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        )}
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.1rem',
                          width: '100%'
                        }}>
                          {player.first_name && (
                            <div style={{
                              fontSize: `${receivedFirstNameSize}rem`,
                              fontWeight: 400,
                              color: 'var(--muted)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.first_name}
                            </div>
                          )}
                          {player.last_name && (
                            <div style={{
                              fontSize: `${receivedLastNameSize}rem`,
                              fontWeight: 600,
                              color: 'var(--text)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.last_name}
                            </div>
                          )}
                        </div>
                      </>
                    ) : (
                      <Link
                        to={`/player/${playerId}`}
                        style={{
                          textDecoration: 'none',
                          display: 'inline-flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.5rem',
                          border: '1px solid transparent',
                          background: 'transparent',
                          borderRadius: '8px',
                          transition: 'all 0.2s ease',
                          cursor: 'pointer',
                          boxSizing: 'border-box'
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
                        {player.image_url && (
                          <img
                            src={player.image_url}
                            alt={playerName}
                            style={{
                              width: `${receivedImageSize}px`,
                              height: `${receivedImageSize}px`,
                              borderRadius: '8px',
                              objectFit: 'cover'
                            }}
                            onError={(e) => {
                              e.target.style.display = 'none';
                            }}
                          />
                        )}
                        <div style={{
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'center',
                          gap: '0.1rem',
                          width: '100%'
                        }}>
                          {player.first_name && (
                            <div style={{
                              fontSize: `${receivedFirstNameSize}rem`,
                              fontWeight: 400,
                              color: 'var(--muted)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.first_name}
                            </div>
                          )}
                          {player.last_name && (
                            <div style={{
                              fontSize: `${receivedLastNameSize}rem`,
                              fontWeight: 600,
                              color: 'var(--accent)',
                              textAlign: 'center',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap',
                              width: '100%'
                            }}>
                              {player.last_name}
                            </div>
                          )}
                        </div>
                      </Link>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
