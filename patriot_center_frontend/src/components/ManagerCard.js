import React from 'react';
import { Link } from 'react-router-dom';

/**
 * ManagerCard - Horizontal card displaying manager summary stats and achievements
 */
export function ManagerCard({ manager }) {
  if (!manager) return null;

  const {
    name,
    image_url,
    years_active = [],
    wins = 0,
    losses = 0,
    ties = 0,
    win_percentage = 0,
    championships = 0,
    playoff_appearances = 0,
    best_finish = null,
    total_trades = 0,
    total_adds = 0,
    total_drops = 0,
    average_points_for = 0,
    is_active = true,
    rankings = {},
    placements = {}
  } = manager;

  // Build record string
  const recordString = ties > 0 ? `${wins}-${losses}-${ties}` : `${wins}-${losses}`;
  const totalGames = wins + losses + ties;

  // Get all rankings
  const allRankings = [];
  const rankingLabels = {
    win_percentage: 'Win %',
    average_points_for: 'PPG',
    trades: 'Trades',
    playoffs: 'Playoffs'
  };

  Object.entries(rankings).forEach(([key, rank]) => {
    if (rankingLabels[key]) {
      allRankings.push({ label: rankingLabels[key], rank });
    }
  });

  // Sort by rank (best to worst)
  allRankings.sort((a, b) => a.rank - b.rank);

  const getRankColor = (rank) => {
    if (rank === 1) return '#FFD700'; // gold
    if (rank === 2) return '#C0C0C0'; // silver
    if (rank === 3) return '#CD7F32'; // bronze
    return 'var(--muted)';
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return '';
  };

  // Get medal counts from placements
  const medalCounts = React.useMemo(() => {
    return {
      gold: placements.first_place || 0,
      silver: placements.second_place || 0,
      bronze: placements.third_place || 0
    };
  }, [placements]);

  // Helper function to format years active (matching ManagerPage)
  const formatYearsActive = (years) => {
    if (!years || years.length === 0) return { yearsText: 'N/A', seasonsText: null };
    if (years.length === 1) return { yearsText: years[0], seasonsText: '(1 season)' };

    const sortedYears = [...years].map(y => Number(y)).sort((a, b) => a - b);
    const first = sortedYears[0];
    const last = sortedYears[sortedYears.length - 1];
    const count = sortedYears.length;

    // Check if years are continuous
    const isContinuous = sortedYears.every((year, i) => {
      if (i === 0) return true;
      return year === sortedYears[i - 1] + 1;
    });

    if (isContinuous) {
      return {
        yearsText: `${first}-${last}`,
        seasonsText: `(${count} season${count !== 1 ? 's' : ''})`
      };
    } else {
      // Show individual years separated by commas
      return {
        yearsText: sortedYears.join(', '),
        seasonsText: `(${count} season${count !== 1 ? 's' : ''})`
      };
    }
  };

  const { yearsText, seasonsText } = formatYearsActive(years_active);

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: '8px',
      overflow: 'hidden',
      width: '100%',
      background: 'var(--card-bg)',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      display: 'flex',
      minHeight: '140px'
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.transform = 'translateY(-2px)';
      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.2)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      {/* Left Section: Image, Name, Years, Record (matching ManagerPage) */}
      <div style={{
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '0.5rem',
        background: 'rgba(255, 255, 255, 0.02)',
        borderRight: '1px solid var(--border)',
        minWidth: '200px',
        flexShrink: 0
      }}>
        {/* Profile Picture with Medal */}
        <div style={{ position: 'relative', marginBottom: '1rem' }}>
          <Link
            to={`/manager/${encodeURIComponent(name)}`}
            style={{ textDecoration: 'none' }}
          >
            <div style={{
              width: '140px',
              height: '140px',
              borderRadius: '50%',
              border: '4px solid var(--border)',
              background: 'var(--bg-alt)',
              overflow: 'hidden',
              transition: 'border-color 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'var(--accent)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)';
            }}
            >
              {image_url && (
                <img
                  src={image_url}
                  alt={name}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover'
                  }}
                  onError={(e) => {
                    e.target.style.display = 'none';
                  }}
                />
              )}
            </div>
          </Link>

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

        {/* Manager Name */}
        <Link
          to={`/manager/${encodeURIComponent(name)}`}
          style={{
            margin: '0.5rem 0 0.5rem 0',
            fontSize: '2rem',
            fontWeight: 700,
            color: 'var(--text)',
            textDecoration: 'none',
            textAlign: 'center',
            transition: 'color 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.color = 'var(--accent)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.color = 'var(--text)';
          }}
        >
          {name}
        </Link>

        {/* Years Active */}
        <div style={{
          color: 'var(--muted)',
          fontSize: '0.95rem',
          textAlign: 'center',
          marginBottom: '0.5rem'
        }}>
          {yearsText}
        </div>
        {seasonsText && (
          <div style={{
            color: 'var(--muted)',
            fontSize: '0.95rem',
            textAlign: 'center'
          }}>
            {seasonsText}
          </div>
        )}

        {/* Record */}
        <div style={{
          color: 'var(--text)',
          fontSize: '1.5rem',
          fontWeight: 700,
          textAlign: 'center'
        }}>
          {recordString}
        </div>

        {/* Inactive label */}
        {!is_active && (
          <div style={{
            fontSize: '0.7rem',
            color: 'var(--muted)',
            fontStyle: 'italic',
            marginTop: '0.25rem'
          }}>
            (Inactive)
          </div>
        )}
      </div>

      {/* Right Section: All Data */}
      <div style={{
        flex: 1,
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem'
      }}>
        {/* Top Row: Win %, Championships */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          paddingBottom: '0.5rem',
          borderBottom: '1px solid var(--border)'
        }}>
          <div style={{
            padding: '0.25rem 0.75rem',
            background: win_percentage >= 50 ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            borderRadius: '12px',
            fontSize: '0.85rem',
            fontWeight: 600,
            color: win_percentage >= 50 ? '#10b981' : '#ef4444'
          }}>
            {win_percentage.toFixed(1)}% Win Rate
          </div>
          <div style={{
            fontSize: '0.75rem',
            color: 'var(--muted)'
          }}>
            {totalGames} games
          </div>
          {championships > 0 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              marginLeft: 'auto',
              padding: '0.25rem 0.75rem',
              background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.2) 0%, rgba(255, 215, 0, 0.1) 100%)',
              borderRadius: '12px',
              border: '1px solid rgba(255, 215, 0, 0.3)'
            }}>
              <div style={{ fontSize: '1.25rem' }}>🏆</div>
              <div style={{
                fontSize: '1rem',
                fontWeight: 700,
                color: '#FFD700'
              }}>
                {championships}
              </div>
            </div>
          )}
        </div>

        {/* Stats Row */}
        <div style={{
          display: 'flex',
          gap: '1.5rem',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Seasons:
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>
              {years_active.length}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Playoffs:
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>
              {playoff_appearances}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              PPG:
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>
              {average_points_for.toFixed(1)}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Trades:
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>
              {total_trades}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Adds:
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>
              {total_adds}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Drops:
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text)' }}>
              {total_drops}
            </div>
          </div>
        </div>

        {/* Bottom Row: Years and Rankings */}
        <div style={{
          display: 'flex',
          gap: '1.5rem',
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          {/* Years */}
          {years_active.length > 0 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <div style={{
                fontSize: '0.65rem',
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Years:
              </div>
              <div style={{
                display: 'flex',
                gap: '0.25rem',
                flexWrap: 'wrap'
              }}>
                {years_active.map((year, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.15rem 0.4rem',
                      background: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid var(--border)',
                      borderRadius: '3px',
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      color: 'var(--text)'
                    }}
                  >
                    {year}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Rankings */}
          {allRankings.length > 0 && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              flexWrap: 'wrap'
            }}>
              <div style={{
                fontSize: '0.65rem',
                color: 'var(--muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Ranks:
              </div>
              {allRankings.map((ranking, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '0.25rem 0.5rem',
                    borderRadius: '12px',
                    fontSize: '0.65rem',
                    fontWeight: 600,
                    background: ranking.rank <= 3 ? `${getRankColor(ranking.rank)}20` : 'rgba(255, 255, 255, 0.05)',
                    color: ranking.rank <= 3 ? getRankColor(ranking.rank) : 'var(--muted)',
                    border: `1px solid ${ranking.rank <= 3 ? getRankColor(ranking.rank) : 'var(--border)'}`,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}
                >
                  {ranking.rank <= 3 && <span style={{ fontSize: '0.75rem' }}>{getRankIcon(ranking.rank)}</span>}
                  <span>#{ranking.rank} {ranking.label}</span>
                </div>
              ))}
            </div>
          )}

          {/* Best Finish (if no championships) */}
          {championships === 0 && best_finish && (
            <div style={{
              fontSize: '0.65rem',
              color: 'var(--muted)',
              fontStyle: 'italic'
            }}>
              {typeof best_finish === 'number' ? (
                <>Best: {best_finish === 1 ? '1st' : best_finish === 2 ? '2nd' : '3rd'}</>
              ) : (
                <>{best_finish}</>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
