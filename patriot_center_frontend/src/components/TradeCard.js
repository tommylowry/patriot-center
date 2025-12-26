import React, { useRef, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

/**
 * TradeCard - Visual trade card showing player movement between managers
 * Layout: All managers on left/right with connecting arrows to player batches
 */
export function TradeCard({ trade, hideHeader = false }) {
  if (!trade) return null;

  const managersInvolved = trade.managers_involved || [];
  const week = trade.week;
  const year = trade.year;
  const containerRef = useRef(null);
  const [, setForceUpdate] = useState(0);

  // Build a list of player movements: { player, from, to }
  const playerMovements = [];

  managersInvolved.forEach(manager => {
    const managerName = typeof manager === 'string' ? manager : manager?.name || 'Unknown';
    const managerImageUrl = typeof manager === 'object' ? manager?.image_url : null;
    const managerKey = managerName.toLowerCase().replace(/\s+/g, '_');
    const sent = trade[`${managerKey}_sent`] || [];

    // For each player this manager sent, find who received it
    sent.forEach(player => {
      // Find which manager received this player
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

  // Group player movements by fromManager -> toManager
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

  // Get unique managers for left and right columns
  const uniqueSendingManagers = new Map();
  const uniqueReceivingManagers = new Map();

  movementGroups.forEach(group => {
    if (!uniqueSendingManagers.has(group.fromManager)) {
      uniqueSendingManagers.set(group.fromManager, {
        name: group.fromManager,
        image: group.fromManagerImage
      });
    }
    if (!uniqueReceivingManagers.has(group.toManager)) {
      uniqueReceivingManagers.set(group.toManager, {
        name: group.toManager,
        image: group.toManagerImage
      });
    }
  });

  const sendingManagers = Array.from(uniqueSendingManagers.values());
  const receivingManagers = Array.from(uniqueReceivingManagers.values());

  // Force update after mount to calculate arrow positions
  useEffect(() => {
    const timer = setTimeout(() => setForceUpdate(v => v + 1), 100);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div style={{
      borderRadius: '8px',
      overflow: 'hidden',
      border: '1px solid var(--border)'
    }}>
      {/* Header */}
      {!hideHeader && week && year && (
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
      <div style={{ padding: '1.5rem', position: 'relative' }} ref={containerRef}>
        <svg style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          zIndex: 0
        }}>
          {/* Draw arrows from managers to batches and batches to managers */}
          {movementGroups.map((group, idx) => {
            const batchElement = containerRef.current?.querySelector(`[data-batch-id="${idx}"]`);
            const fromManagerElement = containerRef.current?.querySelector(`[data-left-manager="${group.fromManager}"]`);
            const toManagerElement = containerRef.current?.querySelector(`[data-right-manager="${group.toManager}"]`);

            // Get the first and last player in this batch
            const firstPlayer = containerRef.current?.querySelector(`[data-batch-player="${idx}-0"]`);
            const lastPlayer = containerRef.current?.querySelector(`[data-batch-player="${idx}-${group.players.length - 1}"]`);

            if (!batchElement || !fromManagerElement || !toManagerElement || !firstPlayer || !lastPlayer || !containerRef.current) return null;

            const containerRect = containerRef.current.getBoundingClientRect();
            const batchRect = batchElement.getBoundingClientRect();
            const fromRect = fromManagerElement.getBoundingClientRect();
            const toRect = toManagerElement.getBoundingClientRect();
            const firstPlayerRect = firstPlayer.getBoundingClientRect();
            const lastPlayerRect = lastPlayer.getBoundingClientRect();

            // Calculate positions relative to container
            const fromX = fromRect.right - containerRect.left;
            const fromY = fromRect.top + fromRect.height / 2 - containerRect.top;
            const batchLeftX = firstPlayerRect.left - containerRect.left;
            const batchRightX = lastPlayerRect.right - containerRect.left;
            const batchY = batchRect.top + batchRect.height / 2 - containerRect.top;
            const toX = toRect.left - containerRect.left;
            const toY = toRect.top + toRect.height / 2 - containerRect.top;

            return (
              <g key={idx}>
                {/* Arrow from manager to left edge of batch */}
                <line
                  x1={fromX + 5}
                  y1={fromY}
                  x2={batchLeftX}
                  y2={batchY}
                  stroke="rgba(255, 255, 255, 0.3)"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                />
                {/* Arrow from right edge of batch to manager */}
                <line
                  x1={batchRightX}
                  y1={batchY}
                  x2={toX - 5}
                  y2={toY}
                  stroke="rgba(255, 255, 255, 0.3)"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                />
              </g>
            );
          })}
          {/* Define arrowhead marker */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="10"
              refX="9"
              refY="3"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3, 0 6"
                fill="rgba(255, 255, 255, 0.3)"
              />
            </marker>
          </defs>
        </svg>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '120px 1fr 120px',
          gap: '3rem',
          alignItems: 'center',
          position: 'relative',
          zIndex: 1
        }}>
          {/* Left Column: All Sending Managers (once each) */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '3rem',
            alignItems: 'center'
          }}>
            {sendingManagers.map((manager, idx) => (
              <Link
                key={idx}
                to={`/manager/${encodeURIComponent(manager.name)}`}
                data-left-manager={manager.name}
                style={{
                  textDecoration: 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {manager.image && (
                  <img
                    src={manager.image}
                    alt={manager.name}
                    style={{
                      width: '80px',
                      height: '80px',
                      borderRadius: '50%',
                      objectFit: 'cover'
                    }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                <div style={{
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--text)',
                  textAlign: 'center'
                }}>
                  {manager.name}
                </div>
              </Link>
            ))}
          </div>

          {/* Middle Column: All Player Batches */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '3rem'
          }}>
            {movementGroups.map((group, idx) => (
              <div
                key={idx}
                data-batch-id={idx}
                style={{
                  display: 'flex',
                  gap: '1rem',
                  justifyContent: 'center',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  minHeight: '80px'
                }}
              >
                {group.players.map((player, playerIdx) => {
                  const playerName = player.name || 'Unknown';
                  const playerSlug = player.slug || encodeURIComponent(playerName.toLowerCase());
                  const isFAAB = playerName.includes('FAAB');

                  return (
                    <div
                      key={playerIdx}
                      data-batch-player={`${idx}-${playerIdx}`}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '0.5rem'
                      }}>
                      {isFAAB ? (
                        <>
                          {player.image_url && (
                            <img
                              src={player.image_url}
                              alt={playerName}
                              style={{
                                width: '70px',
                                height: '70px',
                                borderRadius: '8px',
                                objectFit: 'cover'
                              }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          )}
                          <div style={{
                            fontSize: '0.85rem',
                            fontWeight: 600,
                            color: 'var(--text)',
                            textAlign: 'center',
                            maxWidth: '80px'
                          }}>
                            {playerName}
                          </div>
                        </>
                      ) : (
                        <Link
                          to={`/player/${playerSlug}`}
                          style={{
                            textDecoration: 'none',
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            gap: '0.5rem'
                          }}
                        >
                          {player.image_url && (
                            <img
                              src={player.image_url}
                              alt={playerName}
                              style={{
                                width: '70px',
                                height: '70px',
                                borderRadius: '8px',
                                objectFit: 'cover'
                              }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          )}
                          <div style={{
                            fontSize: '0.85rem',
                            fontWeight: 600,
                            color: 'var(--accent)',
                            textAlign: 'center',
                            maxWidth: '80px'
                          }}>
                            {playerName}
                          </div>
                        </Link>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>

          {/* Right Column: All Receiving Managers (once each) */}
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '3rem',
            alignItems: 'center'
          }}>
            {receivingManagers.map((manager, idx) => (
              <Link
                key={idx}
                to={`/manager/${encodeURIComponent(manager.name)}`}
                data-right-manager={manager.name}
                style={{
                  textDecoration: 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                {manager.image && (
                  <img
                    src={manager.image}
                    alt={manager.name}
                    style={{
                      width: '80px',
                      height: '80px',
                      borderRadius: '50%',
                      objectFit: 'cover'
                    }}
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                )}
                <div style={{
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  color: 'var(--text)',
                  textAlign: 'center'
                }}>
                  {manager.name}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
