import React from 'react';
import { Link } from 'react-router-dom';

/**
 * PlayerLinkVertical - Helper component to display player with image on left, name on right (vertically stacked)
 */
function PlayerLinkVertical({ player, imageSize = 45, fontSize = '0.75rem', faabAmount = null, scaleFactor = 1, isMobile = false }) {
  const playerName = typeof player === 'string' ? player : player?.name || 'Unknown';
  const playerId = typeof player === 'object' ? player?.player_id : null;
  const imageUrl = typeof player === 'object' ? player?.image_url : null;
  const firstName = typeof player === 'object' ? player?.first_name : null;
  const lastName = typeof player === 'object' ? player?.last_name : null;

  // Check if this is FAAB or a draft pick (not a real player)
  const isFAAB = playerName.toLowerCase().includes('faab');
  const isDraftPick = playerName.toLowerCase().includes('draft pick') ||
                      playerName.toLowerCase().includes('round pick') ||
                      /\d{4}\s+(1st|2nd|3rd|4th|5th|6th|7th)\s+round/i.test(playerName);
  const provideLink = typeof player === 'object' ? player?.provide_link : undefined;
  const shouldLink = !isFAAB && !isDraftPick && provideLink !== false;

  if (!shouldLink) {
    // For FAAB and draft picks, render without Link wrapper
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        {imageUrl && (
          <div style={{ position: 'relative', flexShrink: 0 }}>
            <img
              src={imageUrl}
              alt={playerName}
              style={{
                width: `${imageSize}px`,
                height: `${imageSize}px`,
                borderRadius: '8px',
                objectFit: 'cover'
              }}
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            {faabAmount !== null && faabAmount !== undefined && (
              <div style={{
                position: 'absolute',
                bottom: isMobile ? `${-3 * scaleFactor}px` : `${-4 * scaleFactor}px`,
                right: isMobile ? `${-4 * scaleFactor}px` : `${-6 * scaleFactor}px`,
                background: 'tan',
                color: 'black',
                clipPath: 'polygon(20% 0%, 100% 0%, 100% 100%, 20% 100%, 0% 50%)',
                padding: isMobile
                  ? `${2 * scaleFactor}px ${4 * scaleFactor}px ${2 * scaleFactor}px ${6 * scaleFactor}px`
                  : `${3 * scaleFactor}px ${6 * scaleFactor}px ${3 * scaleFactor}px ${8 * scaleFactor}px`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: isMobile ? `${0.5 * scaleFactor}rem` : `${0.6 * scaleFactor}rem`,
                fontWeight: 700,
                border: isMobile ? `${1.5 * scaleFactor}px solid var(--card-bg)` : `${2 * scaleFactor}px solid var(--card-bg)`,
                boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                minWidth: isMobile ? `${20 * scaleFactor}px` : `${24 * scaleFactor}px`,
                height: isMobile ? `${14 * scaleFactor}px` : `${18 * scaleFactor}px`
              }}>
                ${faabAmount}
              </div>
            )}
          </div>
        )}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem', flex: 1, alignItems: 'center' }}>
          {firstName && (
            <div style={{ fontSize: `${parseFloat(fontSize) * 0.85}rem`, fontWeight: 400, color: 'var(--muted)', opacity: 0.7 }}>
              {firstName}
            </div>
          )}
          {lastName && (
            <div style={{ fontSize: fontSize, fontWeight: 600, color: 'var(--text)', opacity: 0.7 }}>
              {lastName}
            </div>
          )}
          {!firstName && !lastName && (
            <div style={{ fontSize: fontSize, fontWeight: 600, color: 'var(--text)', opacity: 0.7 }}>
              {playerName}
            </div>
          )}
        </div>
      </div>
    );
  }

  // For real players, wrap everything in a Link with hover effect
  return (
    <Link
      to={`/player/${playerId}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.25rem',
        border: '1px solid transparent',
        background: 'transparent',
        borderRadius: '8px',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
        textDecoration: 'none',
        color: 'var(--text)'
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
      {imageUrl && (
        <div style={{ position: 'relative', flexShrink: 0 }}>
          <img
            src={imageUrl}
            alt={playerName}
            style={{
              width: `${imageSize}px`,
              height: `${imageSize}px`,
              borderRadius: '8px',
              objectFit: 'cover'
            }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          {faabAmount !== null && faabAmount !== undefined && (
            <div style={{
              position: 'absolute',
              bottom: isMobile ? `${-3 * scaleFactor}px` : `${-4 * scaleFactor}px`,
              right: isMobile ? `${-4 * scaleFactor}px` : `${-6 * scaleFactor}px`,
              background: 'tan',
              color: 'black',
              clipPath: 'polygon(20% 0%, 100% 0%, 100% 100%, 20% 100%, 0% 50%)',
              padding: isMobile
                ? `${2 * scaleFactor}px ${4 * scaleFactor}px ${2 * scaleFactor}px ${6 * scaleFactor}px`
                : `${3 * scaleFactor}px ${6 * scaleFactor}px ${3 * scaleFactor}px ${8 * scaleFactor}px`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: isMobile ? `${0.5 * scaleFactor}rem` : `${0.6 * scaleFactor}rem`,
              fontWeight: 700,
              border: isMobile ? `${1.5 * scaleFactor}px solid var(--card-bg)` : `${2 * scaleFactor}px solid var(--card-bg)`,
              boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
              minWidth: isMobile ? `${20 * scaleFactor}px` : `${24 * scaleFactor}px`,
              height: isMobile ? `${14 * scaleFactor}px` : `${18 * scaleFactor}px`
            }}>
              ${faabAmount}
            </div>
          )}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem', flex: 1, alignItems: 'center' }}>
        {firstName && (
          <div style={{ fontSize: `${parseFloat(fontSize) * 0.85}rem`, fontWeight: 400, color: 'var(--muted)' }}>
            {firstName}
          </div>
        )}
        {lastName && (
          <div style={{ fontSize: fontSize, fontWeight: 600 }}>
            {lastName}
          </div>
        )}
        {!firstName && !lastName && (
          <div style={{ fontSize: fontSize, fontWeight: 600 }}>
            {playerName}
          </div>
        )}
      </div>
    </Link>
  );
}

/**
 * Relationship indicator colors
 */
const RELATIONSHIP_COLORS = {
  add: '#10b981',  // green for adds
  drop: '#ef4444'  // red for drops
};

/**
 * WaiverCard - Weekly waiver card showing all adds/drops for a specific week
 */
export function WaiverCard({ weekData, isMobile = false }) {
  if (!weekData) return null;

  const { year, week, transactions } = weekData;

  // Process transactions: split add_and_drop into separate adds/drops with relationship indicators
  const processedAdds = [];
  const processedDrops = [];

  // First, process all add_and_drop transactions
  const addAndDrops = transactions.filter(t => t.type === 'add_and_drop');
  addAndDrops.forEach((txn, idx) => {
    const relationshipId = `add_drop_${idx}`;

    processedAdds.push({
      player: txn.added_player,
      faab_spent: txn.faab_spent,
      relationshipId: relationshipId,
      relatedPlayer: txn.dropped_player
    });

    processedDrops.push({
      player: txn.dropped_player,
      relationshipId: relationshipId,
      relatedPlayer: txn.added_player
    });
  });

  // Then add standalone adds and drops
  const standaloneAdds = transactions.filter(t => t.type === 'add');
  standaloneAdds.forEach(txn => {
    processedAdds.push({
      player: txn.player,
      faab_spent: txn.faab_spent,
      relationshipId: null,
      relatedPlayer: null
    });
  });

  const standaloneDrops = transactions.filter(t => t.type === 'drop');
  standaloneDrops.forEach(txn => {
    processedDrops.push({
      player: txn.player,
      relationshipId: null,
      relatedPlayer: null
    });
  });

  // Determine which columns have data
  const hasAdds = processedAdds.length > 0;
  const hasDrops = processedDrops.length > 0;

  // Always show both columns
  const activeColumns = 2;

  // Don't render if no transactions at all
  if (transactions.length === 0) return null;

  // Calculate optimal scaling based on longest last name
  const allPlayers = [
    ...processedAdds.map(a => a.player),
    ...processedDrops.map(d => d.player)
  ];

  const longestLastName = allPlayers.reduce((longest, player) => {
    const lastName = typeof player === 'object' ? player?.last_name : null;
    if (!lastName) return longest;
    return lastName.length > longest.length ? lastName : longest;
  }, '');

  // Calculate dimensions - reduced for mobile
  const cardWidth = isMobile ? 375 : 450; // maxWidth
  const contentPadding = isMobile ? 16 : 32;
  const availableWidth = cardWidth - contentPadding;
  const columnWidth = availableWidth / activeColumns;
  const columnPadding = isMobile ? 12 : 24;
  const usableColumnWidth = columnWidth - columnPadding;

  // Base dimensions - reduced for mobile
  const baseImageSize = isMobile ? 35 : 45;
  const baseFontSize = isMobile ? 0.75 : 0.9; // rem
  const baseGap = isMobile ? 6 : 8; // gap between image and text

  // Available space for text (accounting for image and gap)
  const availableForText = usableColumnWidth - baseImageSize - baseGap;

  // Estimate character width at base font size (0.6 is average for most fonts)
  const baseCharWidth = baseFontSize * 16 * 0.6;
  const estimatedNameWidth = longestLastName.length * baseCharWidth;

  // Calculate scale factor to use 85% of available space
  const targetUsage = 0.85;
  const minScale = 0.8;
  const maxScale = 1.4;
  const scaleFactor = estimatedNameWidth > 0
    ? Math.min(Math.max((availableForText * targetUsage) / estimatedNameWidth, minScale), maxScale)
    : 1;

  // Apply scaled dimensions
  const scaledImageSize = Math.round(baseImageSize * scaleFactor);
  const scaledFontSize = parseFloat((baseFontSize * scaleFactor).toFixed(2));

  return (
    <div style={{
      borderRadius: '12px',
      overflow: 'hidden',
      maxWidth: '450px',
      width: '100%'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        marginBottom: isMobile ? '0.35rem' : '0.5rem'
      }}>
        <div style={{
          fontSize: isMobile ? '0.85rem' : '1rem',
          fontWeight: 700,
          letterSpacing: isMobile ? '1px' : '1.5px',
          textTransform: 'uppercase',
          color: 'var(--text)'
        }}>
          {year} Week {week}
        </div>
        <div style={{
          fontSize: isMobile ? '0.65rem' : '0.75rem',
          color: 'var(--muted)',
          marginTop: isMobile ? '0.2rem' : '0.25rem'
        }}>
          {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Content - 2 column layout (Adds and Drops) side by side */}
      <div style={{
        padding: isMobile ? '0.65rem' : '1rem',
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '0'
      }}>
        {/* Adds Column - Always shown */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          paddingRight: isMobile ? '0.5rem' : '0.75rem'
        }}>
          <div style={{
            fontSize: isMobile ? '0.85rem' : '1rem',
            fontWeight: 700,
            color: 'var(--text)',
            marginBottom: isMobile ? '0.5rem' : '0.75rem',
            paddingBottom: isMobile ? '0.35rem' : '0.5rem',
            borderBottom: '1px solid var(--border)'
          }}>
            Adds ({processedAdds.length})
          </div>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: isMobile ? '0.5rem' : '0.65rem',
            width: '100%'
          }}>
            {processedAdds.map((txn, i) => {
              const hasRelationship = txn.relationshipId !== null;
              return (
                <div key={i} style={{ position: 'relative' }}>
                  <PlayerLinkVertical
                    player={txn.player}
                    imageSize={scaledImageSize}
                    fontSize={`${scaledFontSize}rem`}
                    faabAmount={txn.faab_spent}
                    scaleFactor={scaleFactor}
                    isMobile={isMobile}
                  />
                  {hasRelationship && (
                    <div style={{
                      position: 'absolute',
                      right: isMobile ? '-0.4rem' : '-0.75rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: isMobile ? '16px' : '18px',
                      height: isMobile ? '12px' : '14px',
                      background: RELATIONSHIP_COLORS.add,
                      borderRadius: '3px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: isMobile ? '0.6rem' : '0.7rem',
                      fontWeight: 700
                    }}>
                      +
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Drops Column - Always shown */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          paddingLeft: isMobile ? '0.5rem' : '0.75rem',
          borderLeft: '1px solid var(--border)'
        }}>
          <div style={{
            fontSize: isMobile ? '0.85rem' : '1rem',
            fontWeight: 700,
            color: 'var(--text)',
            marginBottom: isMobile ? '0.5rem' : '0.75rem',
            paddingBottom: isMobile ? '0.35rem' : '0.5rem',
            borderBottom: '1px solid var(--border)'
          }}>
            Drops ({processedDrops.length})
          </div>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: isMobile ? '0.5rem' : '0.65rem',
            width: '100%'
          }}>
            {processedDrops.map((txn, i) => {
              const hasRelationship = txn.relationshipId !== null;
              return (
                <div key={i} style={{ position: 'relative', paddingLeft: '0.45rem' }}>
                  <PlayerLinkVertical
                    player={txn.player}
                    imageSize={scaledImageSize}
                    fontSize={`${scaledFontSize}rem`}
                    scaleFactor={scaleFactor}
                    isMobile={isMobile}
                  />
                  {hasRelationship && (
                    <div style={{
                      position: 'absolute',
                      left: isMobile ? '-0.4rem' : '-0.75rem',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: isMobile ? '16px' : '18px',
                      height: isMobile ? '12px' : '14px',
                      background: RELATIONSHIP_COLORS.drop,
                      borderRadius: '3px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontSize: isMobile ? '0.6rem' : '0.7rem',
                      fontWeight: 700
                    }}>
                      −
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
