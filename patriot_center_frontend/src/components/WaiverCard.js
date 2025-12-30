import React from 'react';
import { Link } from 'react-router-dom';

/**
 * PlayerLinkVertical - Helper component to display player with image on left, name on right (vertically stacked)
 */
function PlayerLinkVertical({ player, imageSize = 45, fontSize = '0.75rem', faabAmount = null }) {
  const playerName = typeof player === 'string' ? player : player?.name || 'Unknown';
  const playerSlug = typeof player === 'object' && player?.slug ? player.slug : encodeURIComponent(playerName.toLowerCase());
  const imageUrl = typeof player === 'object' ? player?.image_url : null;
  const firstName = typeof player === 'object' ? player?.first_name : null;
  const lastName = typeof player === 'object' ? player?.last_name : null;

  // Check if this is FAAB or a draft pick (not a real player)
  const isFAAB = playerName.toLowerCase().includes('faab');
  const isDraftPick = playerName.toLowerCase().includes('draft pick') ||
                      playerName.toLowerCase().includes('round pick') ||
                      /\d{4}\s+(1st|2nd|3rd|4th|5th|6th|7th)\s+round/i.test(playerName);
  const shouldLink = !isFAAB && !isDraftPick;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
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
              bottom: '-4px',
              right: '-6px',
              background: 'tan',
              color: 'black',
              clipPath: 'polygon(20% 0%, 100% 0%, 100% 100%, 20% 100%, 0% 50%)',
              padding: '3px 6px 3px 8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.6rem',
              fontWeight: 700,
              border: '2px solid var(--card-bg)',
              boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
              minWidth: '24px',
              height: '18px'
            }}>
              ${faabAmount}
            </div>
          )}
        </div>
      )}
      {shouldLink ? (
        <Link
          to={`/player/${playerSlug}`}
          style={{
            color: 'var(--text)',
            textDecoration: 'none',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.1rem',
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--accent)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text)';
          }}
        >
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
        </Link>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.1rem' }}>
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
      )}
    </div>
  );
}

/**
 * WaiverCard - Weekly waiver card showing all adds/drops for a specific week
 */
export function WaiverCard({ weekData }) {
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

  const activeColumns = [hasAdds, hasDrops].filter(Boolean).length;

  // Don't render if no transactions
  if (activeColumns === 0) return null;

  return (
    <div style={{
      borderRadius: '12px',
      overflow: 'hidden',
      maxWidth: '450px',
      width: '100%'
    }}>
      {/* Header */}
      <div style={{
        padding: '1rem 1.5rem',
        background: 'var(--bg)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ fontSize: '1rem', fontWeight: 600 }}>
          Week {week} • {year}
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
          {transactions.length} transaction{transactions.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Content - 2 column layout (Adds and Drops) */}
      <div style={{
        padding: '1.5rem',
        display: 'grid',
        gridTemplateColumns: `repeat(${activeColumns}, 1fr)`,
        gap: '0',
        minHeight: '200px'
      }}>
        {/* Adds Column */}
        {hasAdds && (
          <div style={{ display: 'flex', flexDirection: 'column', paddingRight: '1rem' }}>
            <div style={{
              fontSize: '1rem',
              fontWeight: 700,
              color: 'var(--text)',
              marginBottom: '1rem',
              paddingBottom: '0.75rem',
              borderBottom: '1px solid var(--border)'
            }}>
              Adds ({processedAdds.length})
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              width: '100%'
            }}>
              {processedAdds.map((txn, i) => (
                <div key={i}>
                  <PlayerLinkVertical
                    player={txn.player}
                    imageSize={45}
                    fontSize="0.9rem"
                    faabAmount={txn.faab_spent}
                  />
                  {/* TODO: Add relationship indicator for txn.relationshipId */}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Drops Column */}
        {hasDrops && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            paddingLeft: hasAdds ? '1rem' : '0',
            borderLeft: hasAdds ? '1px solid var(--border)' : 'none'
          }}>
            <div style={{
              fontSize: '1rem',
              fontWeight: 700,
              color: 'var(--text)',
              marginBottom: '1rem',
              paddingBottom: '0.75rem',
              borderBottom: '1px solid var(--border)'
            }}>
              Drops ({processedDrops.length})
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '1rem',
              width: '100%'
            }}>
              {processedDrops.map((txn, i) => (
                <div key={i}>
                  <PlayerLinkVertical
                    player={txn.player}
                    imageSize={45}
                    fontSize="0.9rem"
                  />
                  {/* TODO: Add relationship indicator for txn.relationshipId */}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
