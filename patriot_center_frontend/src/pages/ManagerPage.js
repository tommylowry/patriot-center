import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useManagerSummary } from '../hooks/useManagerSummary';
import { useManagerAwards } from '../hooks/useManagerAwards';
import { useManagerTransactions } from '../hooks/useManagerTransactions';
import { useManagerYearlyData } from '../hooks/useManagerYearlyData';
import { useHeadToHead } from '../hooks/useHeadToHead';
import { useAggregatedPlayers } from '../hooks/useAggregatedPlayers';
import { MatchupCard } from '../components/MatchupCard';
import { TradeCard } from '../components/TradeCard';

/**
 * ManagerPage - Social media style profile view with ALL manager data
 */
export default function ManagerPage() {
  const { managerName } = useParams();

  const [year] = useState(null);
  const [imageError, setImageError] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [transactionPage, setTransactionPage] = useState(0);
  const [typeFilter, setTypeFilter] = useState('all');
  const transactionsPerPage = 20;

  // Fetch data from ALL endpoints
  const { summary, loading: summaryLoading, error: summaryError } = useManagerSummary(managerName, { year });
  const { awards, loading: awardsLoading } = useManagerAwards(managerName);
  const { transactions: transactionHistory, loading: transactionsLoading } = useManagerTransactions(
    managerName,
    { year, type: typeFilter === 'all' ? undefined : typeFilter, limit: transactionsPerPage, offset: transactionPage * transactionsPerPage }
  );
  const { yearlyData, loading: yearlyLoading } = useManagerYearlyData(managerName, year);

  // Fetch aggregated players for top player cards (all years)
  const { players: aggregatedPlayers } = useAggregatedPlayers(null, null, managerName);

  // Calculate top players from aggregated data
  const topPlayers = React.useMemo(() => {
    if (!aggregatedPlayers || aggregatedPlayers.length === 0) {
      return { highest: null, lowest: null, mostStarted: null };
    }

    const highest = aggregatedPlayers.reduce((max, p) => (p.ffWAR || 0) > (max.ffWAR || 0) ? p : max, aggregatedPlayers[0]);
    const lowest = aggregatedPlayers.reduce((min, p) => (p.ffWAR || 0) < (min.ffWAR || 0) ? p : min, aggregatedPlayers[0]);
    const mostStarted = aggregatedPlayers.reduce((max, p) => {
      if ((p.num_games_started || 0) > (max.num_games_started || 0)) return p;
      if ((p.num_games_started || 0) === (max.num_games_started || 0) && (p.ffWAR || 0) > (max.ffWAR || 0)) return p;
      return max;
    }, aggregatedPlayers[0]);

    return { highest, lowest, mostStarted };
  }, [aggregatedPlayers]);

  React.useEffect(() => {
    setImageError(false);
  }, [managerName]);

  const loading = summaryLoading || awardsLoading || transactionsLoading || (year && yearlyLoading);
  const error = summaryError;

  if (loading && !summary) return <div className="App" style={{ paddingTop: '2rem' }}><p>Loading manager data...</p></div>;
  if (error) return <div className="App" style={{ paddingTop: '2rem' }}><p style={{ color: 'var(--danger)' }}>Error: {error}</p></div>;
  if (!summary) return null;

  // Extract data
  const avatarUrl = summary.image_url;
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
  const rankings = summary.rankings || {};
  const isActiveManager = summary.rankings?.is_active_manager ?? true;
  const awardsData = awards?.awards || {};

  // Calculate medal counts
  const medalCounts = placements.reduce((acc, p) => {
    if (p.placement === 1) acc.gold++;
    else if (p.placement === 2) acc.silver++;
    else if (p.placement === 3) acc.bronze++;
    return acc;
  }, { gold: 0, silver: 0, bronze: 0 });

  // Pagination controls
  const totalPages = transactionHistory ? Math.ceil(transactionHistory.total_count / transactionsPerPage) : 0;

  return (
    <div className="App" style={{ paddingTop: 0, maxWidth: '1400px', margin: '0 auto' }}>
      {/* Profile Info Section */}
      <div style={{ padding: '2rem' }}>
        <div style={{ display: 'flex', gap: '2rem', marginBottom: '1rem', width: '1000px', maxWidth: '1000px', margin: '0 auto 1rem auto' }}>
          {/* Left - Profile Picture and Info */}
          <div style={{ flex: '0 0 18%', display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 0 }}>
            {/* Profile Picture with Medal */}
            <div style={{ position: 'relative', marginBottom: '1rem' }}>
              <div style={{
                width: '140px',
                height: '140px',
                borderRadius: '50%',
                border: '4px solid var(--border)',
                background: 'var(--bg-alt)',
                overflow: 'hidden'
              }}>
                {avatarUrl && !imageError && (
                  <img
                    src={avatarUrl}
                    alt={managerName}
                    onError={() => setImageError(true)}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                  />
                )}
              </div>

              {/* Medal hanging off bottom */}
              {(medalCounts.gold > 0 || medalCounts.silver > 0 || medalCounts.bronze > 0) && (
                <div style={{
                  position: 'absolute',
                  bottom: '-10px',
                  left: '50%',
                  transform: 'translateX(-50%)',
                  display: 'flex',
                  gap: '0.5rem',
                  background: 'var(--bg)',
                  padding: '0.5rem 0.75rem',
                  borderRadius: '20px',
                  border: '2px solid var(--border)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                }}>
                  {medalCounts.gold > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <span style={{ fontSize: '1.25rem' }}>🥇</span>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, opacity: 0.85 }}>×{medalCounts.gold}</span>
                    </div>
                  )}
                  {medalCounts.silver > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <span style={{ fontSize: '1.25rem' }}>🥈</span>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, opacity: 0.85 }}>×{medalCounts.silver}</span>
                    </div>
                  )}
                  {medalCounts.bronze > 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <span style={{ fontSize: '1.25rem' }}>🥉</span>
                      <span style={{ fontSize: '0.9rem', fontWeight: 700, opacity: 0.85 }}>×{medalCounts.bronze}</span>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Manager Info */}
            <h1 style={{ margin: '0.5rem 0 0.5rem 0', fontSize: '2rem', textAlign: 'center' }}>{managerName}</h1>
            <div style={{ color: 'var(--muted)', fontSize: '0.95rem', marginBottom: '0.5rem', textAlign: 'center' }}>
              {formatYearsActive(yearsActive)}
            </div>
            <div style={{ color: 'var(--text)', fontSize: '1.5rem', fontWeight: 700, textAlign: 'center' }}>
              {formatRecord(overall.wins || 0, overall.losses || 0, overall.ties || 0)}
            </div>
          </div>

          {/* Vertical Divider */}
          <div style={{ width: '1px', background: 'var(--border)', flexShrink: 0 }} />

          {/* Right - Player Cards and Stats */}
          <div style={{ flex: '0 0 82%', display: 'flex', flexDirection: 'column', gap: '0.5rem', minWidth: 0, overflow: 'hidden' }}>
            {/* Top Half - Player Cards */}
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', alignContent: 'center', minWidth: 0 }}>
              <PlayerStatCard
                title="Highest ffWAR"
                player={topPlayers.highest}
                stat="ffWAR"
                additionalInfo={topPlayers.highest ? `${topPlayers.highest.num_games_started} starts` : null}
              />
              <PlayerStatCard
                title="Lowest ffWAR"
                player={topPlayers.lowest}
                stat="ffWAR"
                additionalInfo={topPlayers.lowest ? `${topPlayers.lowest.num_games_started} starts` : null}
              />
              <PlayerStatCard
                title="Most Started"
                player={topPlayers.mostStarted}
                stat="num_games_started"
                additionalInfo={topPlayers.mostStarted ? `${topPlayers.mostStarted.ffWAR?.toFixed(3)} ffWAR` : null}
              />
            </div>

            {/* Horizontal Divider */}
            <div style={{ height: '1px', background: 'var(--border)', margin: '0.5rem 0' }} />

            {/* Bottom Half - Stat Cards */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem', justifyContent: 'center' }}>
              {rankings.worst && (
                <div style={{
                  fontSize: '0.7rem',
                  color: 'var(--muted)',
                  textAlign: 'center',
                  letterSpacing: '0.3px'
                }}>
                  {year
                    ? `Note: circle tiles reflect ranking among the ${rankings.worst} managers of the ${year} season`
                    : isActiveManager
                      ? `Note: circle tiles reflect ranking among the ${rankings.worst} active managers`
                      : `Note: circle tiles reflect ranking among the ${rankings.worst} managers all time`
                  }
                </div>
              )}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(6, 1fr)',
                gap: '1rem'
              }}>
                <RankedStatCard title="Win %" value={`${overall.win_percentage?.toFixed(1) || 0}%`} rank={rankings.win_percentage} worst={rankings.worst} />
              <RankedStatCard title="AVG PF" value={overall.average_points_for?.toFixed(2) || 0} rank={rankings.average_points_for} worst={rankings.worst} />
              <RankedStatCard title="AVG PA" value={overall.average_points_against?.toFixed(2) || 0} rank={rankings.average_points_against} worst={rankings.worst} />
              <RankedStatCard
                title="AVG Diff"
                value={((overall.average_points_for || 0) - (overall.average_points_against || 0)).toFixed(2)}
                rank={rankings.average_points_differential}
                worst={rankings.worst}
              />
              <RankedStatCard title="Trades" value={trades.total || 0} rank={rankings.trades} worst={rankings.worst} />
              <RankedStatCard title="Playoffs" value={playoffAppearances} rank={rankings.playoffs} worst={rankings.worst} />
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{
        display: 'flex',
        gap: '0.5rem',
        borderBottom: '2px solid var(--border)',
        marginBottom: '2rem',
        width: '1000px',
        maxWidth: '1000px',
        margin: '0 auto 2rem auto',
        overflowX: 'auto',
        justifyContent: 'center'
      }}>
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'awards', label: 'Awards' },
            { id: 'transactions', label: 'Transactions' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              style={{
                padding: '0.75rem 1.5rem',
                background: 'none',
                border: 'none',
                borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
                color: tab.disabled ? 'var(--muted)' : activeTab === tab.id ? 'var(--accent)' : 'var(--text)',
                cursor: tab.disabled ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                fontWeight: activeTab === tab.id ? 600 : 400,
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                opacity: tab.disabled ? 0.5 : 1
              }}
              onMouseEnter={(e) => {
                if (!tab.disabled && activeTab !== tab.id) {
                  e.currentTarget.style.color = 'var(--accent)';
                }
              }}
              onMouseLeave={(e) => {
                if (!tab.disabled && activeTab !== tab.id) {
                  e.currentTarget.style.color = 'var(--text)';
                }
              }}
            >
              {tab.label}
            </button>
          ))}
      </div>

      {/* Tab Content */}
      <div style={{ width: '1000px', maxWidth: '1000px', margin: '0 auto' }}>
        {activeTab === 'overview' && <OverviewTab
          overall={overall}
          regularSeason={regularSeason}
          playoffs={playoffs}
          trades={trades}
          adds={adds}
          drops={drops}
          faab={faab}
          placements={placements}
          headToHead={summary.head_to_head || {}}
          managerName={managerName}
        />}

        {activeTab === 'awards' && <AwardsTab
          awardsData={awardsData}
          MatchupCard={MatchupCard}
        />}

        {activeTab === 'transactions' && <TransactionsTab
          transactionHistory={transactionHistory}
          transactionPage={transactionPage}
          setTransactionPage={setTransactionPage}
          totalPages={totalPages}
          transactionsPerPage={transactionsPerPage}
          typeFilter={typeFilter}
          setTypeFilter={setTypeFilter}
        />}

        {activeTab === 'weekly' && year && yearlyData && <WeeklyTab
          yearlyData={yearlyData}
          year={year}
          MatchupCard={MatchupCard}
        />}
      </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, color }) {
  return (
    <div style={{
      minWidth: '120px',
      padding: '1rem',
      background: 'var(--bg-alt)',
      borderRadius: '8px',
      border: '1px solid var(--border)',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase' }}>{title}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: color || 'var(--text)', opacity: 0.85 }}>{value}</div>
    </div>
  );
}

// Ranked Stat Card Component - Shows stat with ranking among active managers
function RankedStatCard({ title, value, color, rank, worst }) {
  // Determine rank color based on dynamic thirds
  const getRankColor = (r, w) => {
    if (!r || !w) return 'var(--text)';
    const firstThird = Math.ceil(w / 3);
    const secondThird = Math.ceil((2 * w) / 3);

    if (r <= firstThird) return 'var(--success)';
    if (r <= secondThird) return 'var(--muted)';
    return 'var(--danger)';
  };

  const rankColor = getRankColor(rank, worst);
  const textColor = '#000000'; // Use black text for all circles
  const displayColor = color || rankColor;

  return (
    <div style={{
      textAlign: 'center',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '0.25rem'
    }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', textTransform: 'uppercase' }}>{title}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: displayColor, opacity: 0.85 }}>{value}</div>
      {rank && worst && (
        <div style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          background: rankColor,
          color: textColor,
          fontSize: '0.85rem',
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {rank}
        </div>
      )}
    </div>
  );
}

// Player Stat Card Component - Shows player with their key stat
function PlayerStatCard({ title, player, stat, additionalInfo }) {
  if (!player) {
    return (
      <div style={{
        padding: '1rem',
        background: 'var(--bg-alt)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        textAlign: 'center',
        minHeight: '120px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>Loading...</div>
      </div>
    );
  }

  const playerName = player.key || player.name;

  // The backend flattens nested objects using dot notation
  const playerSlug = player["slug.slug"] || player.slug || encodeURIComponent(playerName.toLowerCase());
  const firstName = player["slug.first_name"] || playerName.split(' ')[0] || playerName;
  const lastName = player["slug.last_name"] || playerName.split(' ').slice(1).join(' ') || '';

  const statValue = stat === 'num_games_started' ? player[stat] : (player[stat]?.toFixed(3) || player[stat] || 0);

  // Determine stat value color based on title
  const getStatValueColor = () => {
    if (title === "Highest ffWAR") return 'var(--success)';
    if (title === "Lowest ffWAR" && parseFloat(statValue) < 0) return 'var(--danger)';
    return 'var(--text)';
  };

  return (
    <div
      style={{
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        minWidth: 0,
        overflow: 'hidden'
      }}
    >
      <div style={{
        fontSize: '1.25rem',
        fontWeight: 700,
        color: 'var(--text)',
        textAlign: 'center',
        letterSpacing: '1px'
      }}>
        {title}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {player.player_image_endpoint && (
          <img
            src={player.player_image_endpoint}
            alt={playerName}
            style={{
              width: '70px',
              height: '70px',
              borderRadius: '8px',
              objectFit: 'cover',
              flexShrink: 0
            }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        )}
        <div style={{ flex: 1, minWidth: 0 }}>
          <Link
            to={`/player/${playerSlug}`}
            style={{
              fontWeight: 600,
              fontSize: '0.95rem',
              color: 'var(--text)',
              textDecoration: 'none',
              overflow: 'hidden',
              lineHeight: '1.2',
              display: 'block',
              transition: 'color 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text)';
            }}
          >
            <div>{firstName}</div>
            <div>{lastName}</div>
          </Link>
          <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
            {player.position} • {player.team}
          </div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: getStatValueColor(), marginTop: '0.25rem', opacity: 0.85 }}>
            {statValue}
          </div>
          {additionalInfo && (
            <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
              {additionalInfo}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// PlayerLink Component - Displays player with image and clickable link
function PlayerLink({ player, showImage = true }) {
  const playerName = typeof player === 'string' ? player : player?.name || 'Unknown';
  const playerSlug = typeof player === 'object' && player?.slug ? player.slug : encodeURIComponent(playerName.toLowerCase());
  const imageUrl = typeof player === 'object' ? player?.image_url : null;

  // Check if this is FAAB or a draft pick (not a real player)
  const isFAAB = playerName.toLowerCase().includes('faab');
  const isDraftPick = playerName.toLowerCase().includes('draft pick') ||
                      playerName.toLowerCase().includes('round pick') ||
                      /\d{4}\s+(1st|2nd|3rd|4th|5th|6th|7th)\s+round/i.test(playerName);
  const shouldLink = !isFAAB && !isDraftPick;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      {showImage && imageUrl && (
        <img
          src={imageUrl}
          alt={playerName}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '4px',
            objectFit: 'cover',
            flexShrink: 0
          }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      )}
      {shouldLink ? (
        <Link
          to={`/player/${playerSlug}`}
          style={{
            color: 'var(--text)',
            textDecoration: 'none',
            fontWeight: 600,
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--accent)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text)';
          }}
        >
          {playerName}
        </Link>
      ) : (
        <span style={{ fontWeight: 600, color: 'var(--text)', opacity: 0.7 }}>
          {playerName}
        </span>
      )}
    </div>
  );
}

// ManagerLink Component - Displays manager with image and clickable link
function ManagerLink({ manager, showImage = true }) {
  const managerName = typeof manager === 'string' ? manager : manager?.name || 'Unknown';
  const imageUrl = typeof manager === 'object' ? manager?.image_url : null;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
      {showImage && imageUrl && (
        <img
          src={imageUrl}
          alt={managerName}
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            objectFit: 'cover',
            border: '2px solid var(--border)',
            flexShrink: 0
          }}
          onError={(e) => {
            e.target.style.display = 'none';
          }}
        />
      )}
      <Link
        to={`/manager/${encodeURIComponent(managerName)}`}
        style={{
          color: 'var(--text)',
          textDecoration: 'none',
          fontWeight: 600,
          transition: 'color 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = 'var(--accent)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = 'var(--text)';
        }}
      >
        {managerName}
      </Link>
    </div>
  );
}

// Helper function to format records (hide ties if 0)
function formatRecord(wins, losses, ties) {
  return ties === 0 ? `${wins}-${losses}` : `${wins}-${losses}-${ties}`;
}

// Helper function to format years active as a compact range
function formatYearsActive(years) {
  if (!years || years.length === 0) return 'N/A';
  if (years.length === 1) return `${years[0]} (1 season)`;

  const sortedYears = [...years].map(y => Number(y)).sort((a, b) => a - b);
  const first = sortedYears[0];
  const last = sortedYears[sortedYears.length - 1];
  const count = sortedYears.length;

  // Check if years are continuous (no gaps)
  const isContinuous = sortedYears.every((year, i) => {
    if (i === 0) return true;
    return year === sortedYears[i - 1] + 1;
  });

  // Show individual years only if there are gaps AND 4 or fewer years
  const yearsText = (!isContinuous && count <= 4)
    ? sortedYears.join(', ')
    : `${first} - ${last}`;

  return (
    <>
      {yearsText}
      <br />
      <span style={{ fontSize: '0.85rem' }}>({count} season{count !== 1 ? 's' : ''})</span>
    </>
  );
}

// Overview Tab
function OverviewTab({ overall, regularSeason, playoffs, trades, adds, drops, faab, placements, headToHead, managerName }) {
  // Sort opponents by wins first, then win percentage as tie breaker
  const sortedOpponents = headToHead ? Object.entries(headToHead).sort((a, b) => {
    // First sort by wins (descending)
    if (b[1].wins !== a[1].wins) {
      return b[1].wins - a[1].wins;
    }
    // If wins are equal, sort by win percentage
    const totalA = a[1].wins + a[1].losses + a[1].ties;
    const totalB = b[1].wins + b[1].losses + b[1].ties;
    const winPctA = totalA > 0 ? (a[1].wins / totalA) : 0;
    const winPctB = totalB > 0 ? (b[1].wins / totalB) : 0;
    return winPctB - winPctA;
  }) : [];

  return (
    <div style={{ display: 'flex', gap: '2rem' }}>
      {/* Left Side - 2 Column Flowing Grid */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: 'repeat(2, minmax(200px, 1fr))', gap: '0.5rem 1rem', alignContent: 'start', minWidth: '680px', maxWidth: '680px' }}>
        {/* Season Stats */}
        <Section title="Season Stats">
          <StatRow label="Regular Season" value={formatRecord(regularSeason.wins || 0, regularSeason.losses || 0, regularSeason.ties || 0)} />
          <StatRow label="Playoffs" value={formatRecord(playoffs.wins || 0, playoffs.losses || 0, playoffs.ties || 0)} />
          <StatRow label="AVG PF" value={overall.average_points_for?.toFixed(2) || 0} />
          <StatRow label="AVG PA" value={overall.average_points_against?.toFixed(2) || 0} />
        </Section>

        {/* Transaction Summary */}
        <Section title="Transactions">
          <StatRow label="Trades" value={trades.total || 0} />
          <StatRow label="Adds" value={adds.total || 0} />
          <StatRow label="Drops" value={drops.total || 0} />
          <StatRow label="FAAB Spent" value={`$${faab.total_spent || 0}`} />
        </Section>

        {/* Placement History */}
        <Section title="Placements">
          {placements.length > 0 ? (
            <div>
              {placements.sort((a, b) => b.year - a.year).map((p, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.25rem 0',
                  borderBottom: i < placements.length - 1 ? '1px solid var(--border)' : 'none'
                }}>
                  <span>{p.year}</span>
                  <span style={{ fontWeight: 700, opacity: 0.85 }}>
                    {p.placement === 1 && '🥇 Champion'}
                    {p.placement === 2 && '🥈 Runner-up'}
                    {p.placement === 3 && '🥉 3rd Place'}
                    {p.placement > 3 && `${p.placement}th`}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: '0.9rem', color: 'var(--muted)', fontStyle: 'italic' }}>
              Manager has never won 1st, 2nd, or 3rd.
            </div>
          )}
        </Section>

        {/* Top Trade Partners */}
        {trades.top_trade_partners && trades.top_trade_partners.length > 0 && (
          <Section title="Top Trade Partners">
            {trades.top_trade_partners.slice(0, 5).map((partner, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <ManagerLink manager={partner} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>{partner.count} trades</span>
              </div>
            ))}
          </Section>
        )}

        {/* Top Players Added */}
        {adds.top_players_added && adds.top_players_added.length > 0 && (
          <Section title="Most Added Players">
            {adds.top_players_added.slice(0, 5).map((player, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <PlayerLink player={player} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
              </div>
            ))}
          </Section>
        )}

        {/* Top Players Dropped */}
        {drops.top_players_dropped && drops.top_players_dropped.length > 0 && (
          <Section title="Most Dropped Players">
            {drops.top_players_dropped.slice(0, 5).map((player, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <PlayerLink player={player} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
              </div>
            ))}
          </Section>
        )}

        {/* Most Acquired via Trade */}
        {trades.most_aquired_players && trades.most_aquired_players.length > 0 && (
          <Section title="Most Acquired (Trade)">
            {trades.most_aquired_players.slice(0, 3).map((player, i) => (
              <div key={i} style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                  <PlayerLink player={player} />
                  <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
                </div>
                {player.from && player.from.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem', paddingLeft: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                    <span>From:</span>
                    {player.from.map((m, j) => (
                      <span key={j} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <ManagerLink manager={m} showImage={false} />
                        <span>({m.count})</span>
                        {j < player.from.length - 1 && <span>,</span>}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </Section>
        )}

        {/* Most Sent via Trade */}
        {trades.most_sent_players && trades.most_sent_players.length > 0 && (
          <Section title="Most Sent (Trade)">
            {trades.most_sent_players.slice(0, 3).map((player, i) => (
              <div key={i} style={{ marginBottom: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                  <PlayerLink player={player} />
                  <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>×{player.count}</span>
                </div>
                {player.to && player.to.length > 0 && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem', paddingLeft: '0.5rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem', alignItems: 'center' }}>
                    <span>To:</span>
                    {player.to.map((m, j) => (
                      <span key={j} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <ManagerLink manager={m} showImage={false} />
                        <span>({m.count})</span>
                        {j < player.to.length - 1 && <span>,</span>}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </Section>
        )}

        {/* FAAB Biggest Acquisitions */}
        {faab.biggest_acquisitions && faab.biggest_acquisitions.length > 0 && (
          <Section title="Biggest FAAB Bids">
            {faab.biggest_acquisitions.map((bid, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.25rem 0', fontSize: '0.95rem' }}>
                <PlayerLink player={bid} />
                <span style={{ fontWeight: 600, color: 'var(--text)', textAlign: 'right', opacity: 0.85 }}>${bid.amount}</span>
              </div>
            ))}
          </Section>
        )}

        {/* FAAB Traded */}
        {faab.faab_traded && (
          <Section title="FAAB Trading">
            <StatRow label="Sent" value={`$${faab.faab_traded.sent || 0}`} color="var(--danger)" />
            <StatRow label="Received" value={`$${faab.faab_traded.received || 0}`} color="var(--success)" />
            <StatRow label="Net" value={`$${faab.faab_traded.net || 0}`} color={faab.faab_traded.net > 0 ? 'var(--success)' : faab.faab_traded.net < 0 ? 'var(--danger)' : undefined} />
          </Section>
        )}
      </div>

      {/* Right Sidebar - Head-to-Head */}
      {sortedOpponents.length > 0 && (
        <div style={{ width: '280px', flexShrink: 0 }}>
            <h3 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: 700, letterSpacing: '1px' }}>Head-to-Head</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {sortedOpponents.map(([opponentKey, data]) => {
              const opponent = data.opponent || { name: opponentKey };
              const totalGames = data.wins + data.losses + data.ties;
              const winPct = totalGames > 0 ? ((data.wins / totalGames) * 100).toFixed(1) : '0.0';
              const tradesCount = data.num_trades_between || 0;
              const pointsFor = data.points_for || 0;
              const pointsAgainst = data.points_against || 0;
              const avgPointsFor = totalGames > 0 ? (pointsFor / totalGames).toFixed(1) : '0.0';
              const avgPointsAgainst = totalGames > 0 ? (pointsAgainst / totalGames).toFixed(1) : '0.0';

              return (
                <Link
                  key={opponentKey}
                  to={`/head-to-head?manager1=${encodeURIComponent(managerName)}&manager2=${encodeURIComponent(opponent.name)}`}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.5rem',
                    padding: '0.75rem',
                    background: 'var(--bg-alt)',
                    borderRadius: '8px',
                    border: '1px solid var(--border)',
                    transition: 'all 0.2s ease',
                    textDecoration: 'none',
                    cursor: 'pointer'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = 'var(--bg)';
                    e.currentTarget.style.borderColor = 'var(--accent)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = 'var(--bg-alt)';
                    e.currentTarget.style.borderColor = 'var(--border)';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <Link
                      to={`/manager/${encodeURIComponent(opponent.name)}`}
                      style={{ flexShrink: 0, display: 'flex', justifyContent: 'center' }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      {opponent.image_url && (
                        <img
                          src={opponent.image_url}
                          alt={opponent.name}
                          style={{
                            width: '64px',
                            height: '64px',
                            borderRadius: '50%',
                            objectFit: 'cover',
                            border: '2px solid var(--border)',
                            cursor: 'pointer'
                          }}
                          onError={(e) => {
                            e.target.style.display = 'none';
                          }}
                        />
                      )}
                    </Link>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <Link
                        to={`/manager/${encodeURIComponent(opponent.name)}`}
                        style={{
                          fontWeight: 600,
                          fontSize: '1rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          color: 'var(--text)',
                          textDecoration: 'none',
                          display: 'block',
                          transition: 'color 0.2s ease'
                        }}
                        onClick={(e) => e.stopPropagation()}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.color = 'var(--accent)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.color = 'var(--text)';
                        }}
                      >
                        {opponent.name}
                      </Link>
                      <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                        <span>{formatRecord(data.wins, data.losses, data.ties)}</span>
                        {' • '}
                        <span style={{
                          fontWeight: 600,
                          color: parseFloat(winPct) >= 50 ? 'var(--success)' : 'var(--danger)',
                          opacity: 0.85
                        }}>
                          {winPct}%
                        </span>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--muted)', marginTop: '0.25rem' }}>
                        <div>Avg: {avgPointsFor} - {avgPointsAgainst}</div>
                        {tradesCount > 0 && (
                          <div>{tradesCount} trade{tradesCount !== 1 ? 's' : ''}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// Head-to-Head Matchup Details Page Component

// Awards Tab - Compact grid layout
function AwardsTab({ awardsData, MatchupCard }) {
  return (
    <div>
      {/* Matchup Awards in 2-column grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Highest Weekly Score */}
        {awardsData.highest_weekly_score && awardsData.highest_weekly_score.manager_1_score > 0 && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--success)' }}>🎯 Highest Weekly Score</h3>
            <MatchupCard matchup={awardsData.highest_weekly_score} />
          </div>
        )}

        {/* Lowest Weekly Score */}
        {awardsData.lowest_weekly_score && awardsData.lowest_weekly_score.manager_1_score < Infinity && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--danger)' }}>📉 Lowest Weekly Score</h3>
            <MatchupCard matchup={awardsData.lowest_weekly_score} />
          </div>
        )}

        {/* Biggest Blowout Win */}
        {awardsData.biggest_blowout_win && awardsData.biggest_blowout_win.differential > 0 && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--success)' }}>💥 Biggest Blowout Win</h3>
            <MatchupCard matchup={awardsData.biggest_blowout_win} showMargin={true} />
          </div>
        )}

        {/* Biggest Blowout Loss */}
        {awardsData.biggest_blowout_loss && awardsData.biggest_blowout_loss.differential < 0 && (
          <div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: 'var(--danger)' }}>😭 Biggest Blowout Loss</h3>
            <MatchupCard matchup={awardsData.biggest_blowout_loss} showMargin={true} />
          </div>
        )}
      </div>

      {/* Activity Awards in horizontal cards */}
      {(awardsData.biggest_faab_bid?.amount > 0 || awardsData.most_trades_in_year?.count > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          {/* Biggest FAAB Bid */}
          {awardsData.biggest_faab_bid && awardsData.biggest_faab_bid.amount > 0 && (
            <div style={{
              padding: '1.5rem',
              background: 'var(--bg-alt)',
              borderRadius: '12px',
              border: '1px solid var(--border)'
            }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', fontWeight: 600 }}>
                💰 Biggest FAAB Bid
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.5rem', opacity: 0.85 }}>
                ${awardsData.biggest_faab_bid.amount}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                {awardsData.biggest_faab_bid.player?.name || awardsData.biggest_faab_bid.player} ({awardsData.biggest_faab_bid.year})
              </div>
            </div>
          )}

          {/* Most Trades in Year */}
          {awardsData.most_trades_in_year && awardsData.most_trades_in_year.count > 0 && (
            <div style={{
              padding: '1.5rem',
              background: 'var(--bg-alt)',
              borderRadius: '12px',
              border: '1px solid var(--border)'
            }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginBottom: '0.75rem', fontWeight: 600 }}>
                🔄 Most Trades (Single Season)
              </div>
              <div style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text)', marginBottom: '0.5rem', opacity: 0.85 }}>
                {awardsData.most_trades_in_year.count}
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                {awardsData.most_trades_in_year.year}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Transactions Tab - SportsCenter Style with Filters
function TransactionsTab({ transactionHistory, transactionPage, setTransactionPage, totalPages, transactionsPerPage, typeFilter, setTypeFilter }) {
  // Reset to page 0 when filter changes
  React.useEffect(() => {
    setTransactionPage(0);
  }, [typeFilter, setTransactionPage]);

  if (!transactionHistory) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>Loading transactions...</div>;
  }

  if (!transactionHistory.transactions || transactionHistory.transactions.length === 0) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
      <p>No transactions found</p>
      <p style={{ fontSize: '0.85rem', marginTop: '0.5rem' }}>Total count: {transactionHistory.total_count || 0}</p>
    </div>;
  }

  return (
    <div>
      {/* Filters and Pagination Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1.5rem',
        padding: '1rem',
        background: 'linear-gradient(135deg, var(--bg-alt) 0%, var(--bg) 100%)',
        borderRadius: '8px',
        border: '1px solid var(--border)',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        {/* Filter Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {['all', 'trade', 'add', 'drop', 'add_and_or_drop'].map(type => (
            <button
              key={type}
              onClick={() => setTypeFilter(type)}
              style={{
                padding: '0.5rem 1rem',
                background: typeFilter === type ? 'var(--accent)' : 'var(--bg)',
                color: typeFilter === type ? 'white' : 'var(--text)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.85rem',
                fontWeight: typeFilter === type ? 600 : 400,
                textTransform: 'capitalize'
              }}
            >
              {type === 'all' && 'All'}
              {type === 'trade' && '🔄 Trades'}
              {type === 'add' && '➕ Adds'}
              {type === 'drop' && '➖ Drops'}
              {type === 'add_and_or_drop' && '🔄 Add/Drop'}
            </button>
          ))}
        </div>

        {/* Pagination */}
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <div style={{ fontSize: '0.85rem', color: 'var(--muted)', marginRight: '0.5rem' }}>
            {transactionPage * transactionsPerPage + 1}-{Math.min((transactionPage + 1) * transactionsPerPage, transactionHistory.total_count)} of {transactionHistory.total_count}
          </div>
          <button
            onClick={() => setTransactionPage(Math.max(0, transactionPage - 1))}
            disabled={transactionPage === 0}
            style={{
              padding: '0.5rem 0.75rem',
              background: transactionPage === 0 ? 'var(--bg)' : 'var(--accent)',
              color: transactionPage === 0 ? 'var(--muted)' : 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: transactionPage === 0 ? 'not-allowed' : 'pointer',
              fontSize: '0.85rem'
            }}
          >
            ←
          </button>
          <div style={{ padding: '0.5rem 0.75rem', background: 'var(--bg)', borderRadius: '6px', fontSize: '0.85rem', minWidth: '80px', textAlign: 'center' }}>
            {transactionPage + 1} / {totalPages}
          </div>
          <button
            onClick={() => setTransactionPage(Math.min(totalPages - 1, transactionPage + 1))}
            disabled={transactionPage >= totalPages - 1}
            style={{
              padding: '0.5rem 0.75rem',
              background: transactionPage >= totalPages - 1 ? 'var(--bg)' : 'var(--accent)',
              color: transactionPage >= totalPages - 1 ? 'var(--muted)' : 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: transactionPage >= totalPages - 1 ? 'not-allowed' : 'pointer',
              fontSize: '0.85rem'
            }}
          >
            →
          </button>
        </div>
      </div>

      {/* Transaction Feed */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {transactionHistory.transactions.map((txn, i) => (
          <div key={i} style={{
            paddingBottom: '1rem',
            borderBottom: '1px solid var(--border)'
          }}>
            {/* Header */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '0.75rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem', color: 'var(--muted)' }}>
                <span>
                  {txn.type === 'trade' && '🔄 Trade'}
                  {txn.type === 'add' && '➕ Add'}
                  {txn.type === 'drop' && '➖ Drop'}
                  {txn.type === 'add_and_or_drop' && '🔄 Add/Drop'}
                </span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                Week {txn.week} • {txn.year}
              </div>
            </div>

            {/* Content */}
            <div>
              {txn.type === 'trade' && (
                <TradeCard trade={txn} />
              )}
              {txn.type === 'add' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <PlayerLink player={txn.player} showImage={true} />
                  {txn.faab_spent !== null && txn.faab_spent !== undefined && (
                    <span style={{ fontSize: '0.9rem', color: 'var(--success)', fontWeight: 700 }}>
                      ${txn.faab_spent} FAAB
                    </span>
                  )}
                </div>
              )}
              {txn.type === 'drop' && (
                <PlayerLink player={txn.player} showImage={true} />
              )}
              {txn.type === 'add_and_or_drop' && (
                <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.95rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--success)', fontSize: '0.8rem' }}>Added:</span>
                    <PlayerLink player={txn.added_player} showImage={true} />
                    {txn.faab_spent !== null && txn.faab_spent !== undefined && (
                      <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                        (${txn.faab_spent})
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ color: 'var(--danger)', fontSize: '0.8rem' }}>Dropped:</span>
                    <PlayerLink player={txn.dropped_player} showImage={true} />
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Weekly Stats Tab - Compact grid layout
function WeeklyTab({ yearlyData, year, MatchupCard }) {
  if (!yearlyData) return null;

  const weeklyScores = yearlyData.matchup_data?.overall?.weekly_scores || [];
  const tradesByWeek = yearlyData.transactions?.trades?.by_week || [];
  const addsByWeek = yearlyData.transactions?.adds?.by_week || [];
  const dropsByWeek = yearlyData.transactions?.drops?.by_week || [];

  // Filter out weeks where the manager didn't play (empty matchup_data)
  const validWeeklyScores = weeklyScores.filter(week =>
    week.manager_1 && week.manager_2 && week.manager_1_score !== undefined && week.manager_2_score !== undefined
  );

  return (
    <div>
      <h3 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '1px' }}>Week-by-Week Breakdown for {year}</h3>

      {/* Weekly Matchups in 2-column grid */}
      {validWeeklyScores.length > 0 && (
        <Section title="📅 Weekly Matchups">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1rem' }}>
            {validWeeklyScores.map((matchup, i) => (
              <MatchupCard
                key={i}
                matchup={matchup}
              />
            ))}
          </div>
        </Section>
      )}

      {/* Weekly Trades */}
      {tradesByWeek.length > 0 && tradesByWeek.some(w => w.trades && w.trades.length > 0) && (
        <Section title="🔄 Trades by Week" style={{ marginTop: '2rem' }}>
          {tradesByWeek.filter(w => w.trades && w.trades.length > 0).map((weekData, i) => (
            <div key={i} style={{ marginBottom: '1rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text)' }}>Week {weekData.week}</div>
              {weekData.trades.map((trade, j) => (
                <div key={j} style={{
                  paddingBottom: '0.75rem',
                  marginBottom: '0.75rem',
                  borderBottom: j < weekData.trades.length - 1 ? '1px solid var(--border)' : 'none'
                }}>
                  <TradeCard trade={trade} />
                </div>
              ))}
            </div>
          ))}
        </Section>
      )}

      {/* Weekly Adds */}
      {addsByWeek.length > 0 && addsByWeek.some(w => w.players && w.players.length > 0) && (
        <Section title="➕ Adds by Week" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.75rem' }}>
            {addsByWeek.filter(w => w.players && w.players.length > 0).map((weekData, i) => (
              <div key={i} style={{
                padding: '0.75rem',
                background: 'var(--bg-alt)',
                borderRadius: '6px',
                border: '1px solid var(--border)'
              }}>
                <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.85rem' }}>Week {weekData.week}</div>
                <div style={{ fontSize: '0.8rem' }}>
                  {weekData.players.map((p, j) => <div key={j}>{typeof p === 'string' ? p : p?.name || 'Unknown Player'}</div>)}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Weekly Drops */}
      {dropsByWeek.length > 0 && dropsByWeek.some(w => w.players && w.players.length > 0) && (
        <Section title="➖ Drops by Week" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '0.75rem' }}>
            {dropsByWeek.filter(w => w.players && w.players.length > 0).map((weekData, i) => (
              <div key={i} style={{
                padding: '0.75rem',
                background: 'var(--bg-alt)',
                borderRadius: '6px',
                border: '1px solid var(--border)'
              }}>
                <div style={{ fontWeight: 700, marginBottom: '0.5rem', fontSize: '0.85rem' }}>Week {weekData.week}</div>
                <div style={{ fontSize: '0.8rem' }}>
                  {weekData.players.map((p, j) => <div key={j}>{typeof p === 'string' ? p : p?.name || 'Unknown Player'}</div>)}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// Section Component
function Section({ title, children, style }) {
  return (
    <div style={{ ...style }}>
      <h3 style={{ marginBottom: '0.75rem', fontSize: '1.25rem', fontWeight: 700, color: 'var(--text)', letterSpacing: '1px' }}>{title}</h3>
      {children}
    </div>
  );
}

// StatRow Component
function StatRow({ label, value, color, small }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0.25rem 0',
      fontSize: small ? '0.85rem' : '0.95rem'
    }}>
      <span style={{ color: 'var(--muted)' }}>{label}</span>
      <span style={{ fontWeight: 600, color: color || 'var(--text)', opacity: 0.85 }}>{value}</span>
    </div>
  );
}
