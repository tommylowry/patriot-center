import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useManagerSummary } from '../hooks/useManagerSummary';
import { useManagerAwards } from '../hooks/useManagerAwards';
import { useManagerTransactions } from '../hooks/useManagerTransactions';
import { useManagerYearlyData } from '../hooks/useManagerYearlyData';

/**
 * ManagerPage - COMPREHENSIVE detail view showing ALL manager data from ALL endpoints
 */
export default function ManagerPage() {
  const { managerName } = useParams();
  const navigate = useNavigate();

  const [year, setYear] = useState(null);
  const [imageError, setImageError] = useState(false);

  // Fetch data from ALL endpoints
  const { summary, loading: summaryLoading, error: summaryError } = useManagerSummary(managerName, { year });
  const { awards, loading: awardsLoading } = useManagerAwards(managerName);
  const { transactions: transactionHistory, loading: transactionsLoading } = useManagerTransactions(managerName, { year, limit: 20 });
  const { yearlyData, loading: yearlyLoading } = useManagerYearlyData(managerName, year);

  React.useEffect(() => {
    setImageError(false);
  }, [managerName]);

  const loading = summaryLoading || awardsLoading || transactionsLoading || (year && yearlyLoading);
  const error = summaryError;

  if (loading && !summary) return <div className="App" style={{ paddingTop: '2rem' }}><p>Loading manager data...</p></div>;
  if (error) return <div className="App" style={{ paddingTop: '2rem' }}><p style={{ color: 'var(--danger)' }}>Error: {error}</p></div>;
  if (!summary) return null;

  // Extract data
  const avatarUrl = summary.avatar_urls?.full_size;
  const yearsActive = summary.years_active || [];
  const overall = summary.matchup_data?.overall || {};
  const regularSeason = summary.matchup_data?.regular_season || {};
  const playoffs = summary.matchup_data?.playoffs || {};
  const transactions = summary.transactions || {};
  const trades = transactions.trades || {};
  const adds = transactions.adds || {};
  const drops = transactions.drops || {};
  const faab = transactions.faab || {};
  const overallData = summary.overall_data || {};
  const placements = overallData.placements || [];
  const playoffAppearances = overallData.playoff_appearances || 0;
  const championships = overallData.championships || 0;
  const headToHead = summary.head_to_head || {};

  // Awards data
  const awardsData = awards?.awards || {};

  // Count medal types
  const medalCounts = placements.reduce((acc, p) => {
    if (p.placement === 1) acc.gold++;
    else if (p.placement === 2) acc.silver++;
    else if (p.placement === 3) acc.bronze++;
    return acc;
  }, { gold: 0, silver: 0, bronze: 0 });

  // Helper components
  const StatCard = ({ title, value, subtitle, color }) => (
    <div style={{
      background: 'var(--bg-alt)',
      padding: '1rem',
      borderRadius: '8px',
      border: '1px solid var(--border)',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</div>
      <div style={{ fontSize: '1.75rem', fontWeight: 700, color: color || 'var(--text)', marginBottom: '0.25rem' }}>{value}</div>
      {subtitle && <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{subtitle}</div>}
    </div>
  );

  const Section = ({ title, children, fullWidth = false }) => (
    <div style={{ marginBottom: '2rem', gridColumn: fullWidth ? '1 / -1' : 'auto' }}>
      <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem', borderBottom: '2px solid var(--border)', paddingBottom: '0.5rem' }}>{title}</h2>
      {children}
    </div>
  );

  return (
    <div className="App" style={{ paddingTop: '1rem', maxWidth: '1800px', margin: '0 auto' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <button onClick={() => navigate(-1)} style={{
          background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '1rem', padding: '0.5rem 1rem'
        }}>← Back</button>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <label htmlFor="year-select" style={{ color: 'var(--muted)' }}>Season:</label>
          <select id="year-select" value={year || 'ALL'} onChange={(e) => setYear(e.target.value === 'ALL' ? null : e.target.value)}
            style={{ background: 'var(--bg-alt)', color: 'var(--text)', border: '1px solid var(--border)', padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer' }}>
            <option value="ALL">All Seasons</option>
            {yearsActive.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>

      {/* Hero */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem', marginBottom: '2rem', padding: '1.5rem', background: 'var(--bg-alt)', borderRadius: '12px', border: '1px solid var(--border)' }}>
        {avatarUrl && !imageError && (
          <img src={avatarUrl} alt={managerName} onError={() => setImageError(true)}
            style={{ width: '120px', height: '120px', objectFit: 'cover', borderRadius: '50%', border: '3px solid var(--border)', flexShrink: 0 }} />
        )}
        <div style={{ flex: 1 }}>
          <h1 style={{ margin: '0 0 0.5rem 0', fontSize: '2.25rem' }}>{managerName}</h1>
          <div style={{ color: 'var(--muted)', fontSize: '1rem', marginBottom: '0.75rem' }}>
            Years Active: {yearsActive.join(', ')}
          </div>
          {(medalCounts.gold > 0 || medalCounts.silver > 0 || medalCounts.bronze > 0) && (
            <div style={{ display: 'flex', gap: '1.5rem' }}>
              {medalCounts.gold > 0 && <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ fontSize: '2rem' }}>🥇</span><span style={{ fontSize: '1.5rem', fontWeight: 700 }}>×{medalCounts.gold}</span></div>}
              {medalCounts.silver > 0 && <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ fontSize: '2rem' }}>🥈</span><span style={{ fontSize: '1.5rem', fontWeight: 700 }}>×{medalCounts.silver}</span></div>}
              {medalCounts.bronze > 0 && <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}><span style={{ fontSize: '2rem' }}>🥉</span><span style={{ fontSize: '1.5rem', fontWeight: 700 }}>×{medalCounts.bronze}</span></div>}
            </div>
          )}
        </div>
      </div>

      {/* Main Grid Layout - 3 Columns */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '2rem' }}>

        {/* COLUMN 1: Matchup Stats */}
        <div>
          <Section title="📊 Matchup Statistics">
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              <StatCard title="Overall" value={overall.record || '0-0-0'} subtitle={`${overall.win_percentage?.toFixed(1) || 0}% Win`} />
              <StatCard title="PF" value={overall.total_points_for?.toFixed(2) || 0} subtitle={`Avg: ${overall.average_points_for?.toFixed(2) || 0}`} />
              <StatCard title="PA" value={overall.total_points_against?.toFixed(2) || 0} subtitle={`Avg: ${overall.average_points_against?.toFixed(2) || 0}`} />
              <StatCard title="Diff" value={(overall.point_differential || 0).toFixed(2)} color={(overall.point_differential || 0) >= 0 ? 'var(--success)' : 'var(--danger)'} subtitle={`Avg: ${(overall.average_point_differential || 0).toFixed(2)}`} />
            </div>
          </Section>

          <Section title="🏈 Regular Season">
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              <StatCard title="Record" value={regularSeason.record || '0-0-0'} subtitle={`${regularSeason.win_percentage?.toFixed(1) || 0}%`} />
              <StatCard title="PF" value={regularSeason.total_points_for?.toFixed(2) || 0} />
              <StatCard title="PA" value={regularSeason.total_points_against?.toFixed(2) || 0} />
            </div>
          </Section>

          <Section title="🏆 Playoffs">
            <div style={{ display: 'grid', gap: '0.75rem' }}>
              <StatCard title="Record" value={playoffs.record || '0-0-0'} />
              <StatCard title="Appearances" value={playoffAppearances} />
              <StatCard title="Championships" value={championships} color="var(--accent)" />
            </div>
          </Section>

          {placements.length > 0 && (
            <Section title="📅 Placement History">
              <div style={{ background: 'var(--bg-alt)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', maxHeight: '300px', overflowY: 'auto' }}>
                {placements.sort((a, b) => b.year - a.year).map((p, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: i < placements.length - 1 ? '1px solid var(--border)' : 'none', fontSize: '0.9rem' }}>
                    <span>{p.year}</span>
                    <span style={{ fontWeight: 700 }}>
                      {p.placement === 1 && '🥇 Champion'}
                      {p.placement === 2 && '🥈 Runner-up'}
                      {p.placement === 3 && '🥉 3rd Place'}
                      {p.placement > 3 && `${p.placement}th`}
                    </span>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>

        {/* COLUMN 2: Transactions */}
        <div>
          <Section title="💼 Transaction Summary">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <StatCard title="Trades" value={trades.total || 0} />
              <StatCard title="Adds" value={adds.total || 0} />
              <StatCard title="Drops" value={drops.total || 0} />
              <StatCard title="FAAB $" value={`$${faab.total_spent || 0}`} />
            </div>
          </Section>

          {trades.top_trade_partners && trades.top_trade_partners.length > 0 && (
            <Section title="🤝 Top Trade Partners">
              <div style={{ background: 'var(--bg-alt)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                {trades.top_trade_partners.slice(0, 5).map((partner, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: i < 4 ? '1px solid var(--border)' : 'none', fontSize: '0.9rem' }}>
                    <span>{partner.name}</span>
                    <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{partner.count}</span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {trades.most_aquired_players && trades.most_aquired_players.length > 0 && (
            <Section title="📈 Most Acquired">
              <div style={{ background: 'var(--bg-alt)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.85rem' }}>
                {trades.most_aquired_players.slice(0, 5).map((player, i) => (
                  <div key={i} style={{ padding: '0.5rem 0', borderBottom: i < 4 ? '1px solid var(--border)' : 'none' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span>{player.name}</span>
                      <span style={{ fontWeight: 700 }}>×{player.count}</span>
                    </div>
                    {player.from && <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                      From: {Object.entries(player.from).map(([n, c]) => `${n} (${c})`).join(', ')}
                    </div>}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {trades.most_sent_players && trades.most_sent_players.length > 0 && (
            <Section title="📉 Most Sent">
              <div style={{ background: 'var(--bg-alt)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border)', fontSize: '0.85rem' }}>
                {trades.most_sent_players.slice(0, 5).map((player, i) => (
                  <div key={i} style={{ padding: '0.5rem 0', borderBottom: i < 4 ? '1px solid var(--border)' : 'none' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                      <span>{player.name}</span>
                      <span style={{ fontWeight: 700 }}>×{player.count}</span>
                    </div>
                    {player.to && <div style={{ fontSize: '0.75rem', color: 'var(--muted)' }}>
                      To: {Object.entries(player.to).map(([n, c]) => `${n} (${c})`).join(', ')}
                    </div>}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {faab.faab_traded && (
            <Section title="💸 FAAB Trading">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
                <StatCard title="Sent" value={`$${faab.faab_traded.sent || 0}`} color="var(--danger)" />
                <StatCard title="Rcvd" value={`$${faab.faab_traded.received || 0}`} color="var(--success)" />
                <StatCard title="Net" value={`$${faab.faab_traded.net || 0}`} color={faab.faab_traded.net > 0 ? 'var(--success)' : faab.faab_traded.net < 0 ? 'var(--danger)' : 'var(--text)'} />
              </div>
            </Section>
          )}
        </div>

        {/* COLUMN 3: Awards & Records */}
        <div>
          {awardsData && (
            <>
              {awardsData.highest_weekly_score && (
                <Section title="🎯 Highest Weekly Score">
                  <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--success)', marginBottom: '0.5rem' }}>
                      {awardsData.highest_weekly_score.score?.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                      Week {awardsData.highest_weekly_score.week}, {awardsData.highest_weekly_score.year} vs {awardsData.highest_weekly_score.opponent}
                    </div>
                  </div>
                </Section>
              )}

              {awardsData.lowest_weekly_score && (
                <Section title="📉 Lowest Weekly Score">
                  <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--danger)', marginBottom: '0.5rem' }}>
                      {awardsData.lowest_weekly_score.score?.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                      Week {awardsData.lowest_weekly_score.week}, {awardsData.lowest_weekly_score.year} vs {awardsData.lowest_weekly_score.opponent}
                    </div>
                  </div>
                </Section>
              )}

              {awardsData.biggest_blowout_win && (
                <Section title="💥 Biggest Blowout Win">
                  <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--success)', marginBottom: '0.5rem' }}>
                      +{awardsData.biggest_blowout_win.differential?.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                      Week {awardsData.biggest_blowout_win.week}, {awardsData.biggest_blowout_win.year} vs {awardsData.biggest_blowout_win.opponent}
                    </div>
                  </div>
                </Section>
              )}

              {awardsData.biggest_blowout_loss && (
                <Section title="😭 Biggest Blowout Loss">
                  <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--danger)', marginBottom: '0.5rem' }}>
                      {awardsData.biggest_blowout_loss.differential?.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                      Week {awardsData.biggest_blowout_loss.week}, {awardsData.biggest_blowout_loss.year} vs {awardsData.biggest_blowout_loss.opponent}
                    </div>
                  </div>
                </Section>
              )}

              {awardsData.biggest_faab_bid && (
                <Section title="💰 Biggest FAAB Bid">
                  <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '0.5rem' }}>
                      ${awardsData.biggest_faab_bid.amount}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                      {awardsData.biggest_faab_bid.player} ({awardsData.biggest_faab_bid.year})
                    </div>
                  </div>
                </Section>
              )}

              {awardsData.most_trades_in_year && (
                <Section title="🔄 Most Trades (Single Season)">
                  <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--accent)', marginBottom: '0.5rem' }}>
                      {awardsData.most_trades_in_year.count}
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                      {awardsData.most_trades_in_year.year}
                    </div>
                  </div>
                </Section>
              )}
            </>
          )}
        </div>

        {/* FULL WIDTH: Head-to-Head */}
        {Object.keys(headToHead).length > 0 && (
          <Section title="⚔️ Head-to-Head Records" fullWidth>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem' }}>
              {Object.entries(headToHead).sort((a, b) => b[1].wins - a[1].wins).map(([opponent, data]) => (
                <div key={opponent} style={{ padding: '1rem', background: 'var(--bg-alt)', borderRadius: '8px', border: '1px solid var(--border)' }}>
                  <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '1.05rem' }}>{opponent}</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem' }}>
                    <div><span style={{ color: 'var(--muted)' }}>Record:</span> <span style={{ fontWeight: 600 }}>{data.wins}-{data.losses}-{data.ties}</span></div>
                    <div><span style={{ color: 'var(--muted)' }}>Win%:</span> <span style={{ fontWeight: 600 }}>{((data.wins / (data.wins + data.losses + data.ties || 1)) * 100).toFixed(1)}%</span></div>
                    <div><span style={{ color: 'var(--muted)' }}>PF:</span> {data.points_for?.toFixed(2) || 0}</div>
                    <div><span style={{ color: 'var(--muted)' }}>PA:</span> {data.points_against?.toFixed(2) || 0}</div>
                  </div>
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* FULL WIDTH: Recent Transactions */}
        {transactionHistory && transactionHistory.transactions && transactionHistory.transactions.length > 0 && (
          <Section title={`📋 Recent Transactions (${transactionHistory.total_count} total)`} fullWidth>
            <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)', maxHeight: '500px', overflowY: 'auto' }}>
              {transactionHistory.transactions.map((txn, i) => (
                <div key={i} style={{ padding: '0.75rem 0', borderBottom: i < transactionHistory.transactions.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <span style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: '0.85rem' }}>
                      {txn.type === 'trade' && '🔄 Trade'}
                      {txn.type === 'add' && '➕ Add'}
                      {txn.type === 'drop' && '➖ Drop'}
                      {txn.type === 'add_and_drop' && '🔄 Add/Drop'}
                    </span>
                    <span style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
                      Week {txn.week}, {txn.year}
                    </span>
                  </div>
                  {txn.type === 'trade' && (
                    <div style={{ fontSize: '0.9rem' }}>
                      <div><strong>With:</strong> {txn.partners?.join(', ')}</div>
                      <div><strong>Acquired:</strong> {txn.acquired?.join(', ')}</div>
                      <div><strong>Sent:</strong> {txn.sent?.join(', ')}</div>
                    </div>
                  )}
                  {txn.type === 'add' && (
                    <div style={{ fontSize: '0.9rem' }}>
                      <strong>Player:</strong> {txn.player} {txn.faab_spent !== null && txn.faab_spent !== undefined && `($${txn.faab_spent})`}
                    </div>
                  )}
                  {txn.type === 'drop' && (
                    <div style={{ fontSize: '0.9rem' }}>
                      <strong>Player:</strong> {txn.player}
                    </div>
                  )}
                  {txn.type === 'add_and_drop' && (
                    <div style={{ fontSize: '0.9rem' }}>
                      <div><strong>Added:</strong> {txn.added_player} {txn.faab_spent !== null && txn.faab_spent !== undefined && `($${txn.faab_spent})`}</div>
                      <div><strong>Dropped:</strong> {txn.dropped_player}</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Section>
        )}

        {/* FULL WIDTH: Weekly Scores (if year selected) */}
        {yearlyData && yearlyData.matchup_data?.overall?.weekly_scores && (
          <Section title={`📅 ${year} Weekly Breakdown`} fullWidth>
            <div style={{ background: 'var(--bg-alt)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border)', maxHeight: '500px', overflowY: 'auto' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '0.75rem' }}>
                {yearlyData.matchup_data.overall.weekly_scores.map((week, i) => (
                  <div key={i} style={{ padding: '0.75rem', background: 'var(--bg)', borderRadius: '6px', border: '1px solid var(--border)' }}>
                    <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.9rem' }}>Week {week.week}</div>
                    <div style={{ fontSize: '0.85rem', marginBottom: '0.25rem' }}>vs {week.opponent}</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                      <span style={{ fontWeight: 600 }}>{week.points_for?.toFixed(2)}</span>
                      <span style={{ color: week.result === 'win' ? 'var(--success)' : week.result === 'loss' ? 'var(--danger)' : 'var(--text)' }}>
                        {week.result === 'win' && 'W'}
                        {week.result === 'loss' && 'L'}
                        {week.result === 'tie' && 'T'}
                      </span>
                      <span>{week.points_against?.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </Section>
        )}

      </div>
    </div>
  );
}
