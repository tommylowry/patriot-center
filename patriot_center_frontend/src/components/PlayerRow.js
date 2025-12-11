import React from 'react';
import { Link } from 'react-router-dom';
import { toPlayerSlug } from './player/PlayerNameFormatter';

export function displayFromSlug(slug) {
  if (!slug) return '';
  const decoded = decodeURIComponent(slug);
  return decoded
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

export function PlayerRow({ player }) {
  const slug = toPlayerSlug(player.key); // preserves capitalization
  const war = Number(player.ffWAR);
  const warClass = war > 0 ? 'war-positive' : war < 0 ? 'war-negative' : 'war-neutral';

  return (
    <tr>
      <td align="center">
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
          <Link to={`/player/${slug}`} style={{ fontWeight: 500 }}>{player.key}</Link>
          <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
            {player.position}{player.team ? ` • ${player.team}` : ''}
          </span>
        </div>
      </td>
      <td align="center">{player.position}</td>
      <td align="center">{player.total_points}</td>
      <td align="center">{player.num_games_started}</td>
      <td align="center" className={warClass}>{player.ffWAR}</td>
    </tr>
  );
}