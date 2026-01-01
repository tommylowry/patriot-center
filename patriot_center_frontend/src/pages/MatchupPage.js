import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, useLocation } from 'react-router-dom';
import { MatchupCard } from '../components/MatchupCard';

/**
 * MatchupPage - Displays a single matchup card for mobile users
 * Receives matchup data through React Router state
 */
export default function MatchupPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isMobile = windowWidth < 768;
  const year = searchParams.get('year');
  const week = searchParams.get('week');

  // Get matchup data from location state (passed from Link)
  const matchup = location.state?.matchup;
  const showMargin = location.state?.showMargin || false;

  if (!matchup || !year || !week) {
    return (
      <div className="App" style={{ paddingTop: '2rem' }}>
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--muted)' }}>
          No matchup data available
        </div>
        <div style={{ textAlign: 'center', marginTop: '1rem' }}>
          <button
            onClick={() => navigate(-1)}
            style={{
              padding: '0.5rem 1rem',
              background: 'var(--accent)',
              border: 'none',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '0.95rem',
              fontWeight: 600
            }}
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="App" style={{ paddingTop: '2rem' }}>
      {/* Back button */}
      <div style={{ marginBottom: '1.5rem', textAlign: 'center', padding: '0 1rem' }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            padding: '0.5rem 1rem',
            background: 'var(--bg-alt)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            color: 'var(--text)',
            cursor: 'pointer',
            fontSize: '0.95rem',
            fontWeight: 600,
            transition: 'all 0.2s ease'
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
          ← Back
        </button>
      </div>

      {/* Matchup card */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        padding: '0 0.5rem',
        maxWidth: '100%',
        overflow: 'hidden'
      }}>
        <div style={{ width: '100%', maxWidth: isMobile ? '100%' : '450px' }}>
          <MatchupCard matchup={matchup} showMargin={showMargin} isMobile={isMobile} />
        </div>
      </div>
    </div>
  );
}
