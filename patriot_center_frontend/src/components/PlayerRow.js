import React from 'react';
import { Link } from 'react-router-dom';

export function PlayerRow({ player }) {
  const war = Number(player.ffWAR);
  const warClass = war > 0 ? 'war-positive' : war < 0 ? 'war-negative' : 'war-neutral';
  const displayName = player.full_name || player.key;

  return (
    <tr>
      <td align="center">
        <div className="player-info" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
          <Link to={`/player/${player.player_id}`} style={{ fontWeight: 500 }}>{displayName}</Link>
          <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
            {player.position}{player.team ? ` • ${player.team}` : ''}
          </span>
        </div>
      </td>
      <td align="center" className="col-position">{player.position}</td>
      <td align="center">{player.total_points}</td>
      <td align="center">{player.num_games_started}</td>
      <td align="center">{Number(player.ffWAR_per_game).toFixed(3)}</td>
      <td align="center" className={warClass}>{player.ffWAR}</td>
    </tr>
  );
}
