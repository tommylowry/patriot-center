import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import SearchBar from './SearchBar';

/**
 * CRITICAL NAVIGATION PATTERN:
 *
 * - "Patriot Center Database" title uses React Router <Link> to navigate to home (Managers page)
 * - "Players" tab uses plain <a> tag to ensure full page reload to /players?year=2025
 * - "Managers" tab uses React Router <Link> since it's a different route (/managers)
 *
 * DO NOT change the Players <a> tag to React Router Link - it will break navigation!
 */
export default function Layout({ children }) {
    const location = useLocation();
    return (
        <div style={{ position: 'relative', minHeight: '100vh' }}>
            {/* Header with Title and Search Bar */}
            <div className="layout-header" style={{
                position: 'sticky',
                top: 0,
                zIndex: 100,
                backgroundColor: 'var(--bg)',
                borderBottom: '1px solid var(--border)',
                paddingBottom: 0
            }}>
                <div style={{
                    padding: '1rem 2rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '2rem'
                }}>
                    {/* Centered Title */}
                    <div style={{ flex: 1 }} className="layout-spacer" />
                    <Link
                        to="/"
                        className="layout-title"
                        style={{
                            textDecoration: 'none',
                            color: 'var(--text)',
                            fontSize: '1.5rem',
                            fontWeight: 600,
                            whiteSpace: 'nowrap'
                        }}
                    >
                        Patriot Center Database
                    </Link>
                    {/* Search Bar on Right */}
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }} className="layout-search-container">
                        <SearchBar />
                    </div>
                </div>

                {/* Navigation Tabs */}
                <div className="nav-tabs" style={{
                    display: 'flex',
                    justifyContent: 'center',
                    gap: '0.5rem',
                    padding: '0 2rem',
                    borderTop: '1px solid var(--border)'
                }}>
                    <a
                        href="/players?year=2025"
                        style={{
                            padding: '0.75rem 1.5rem',
                            textDecoration: 'none',
                            color: 'var(--text)',
                            fontWeight: 500,
                            borderBottom: location.pathname === '/players' ? '2px solid var(--accent)' : '2px solid transparent',
                            transition: 'all 0.2s ease'
                        }}
                    >
                        Players
                    </a>
                    <Link
                        to="/managers"
                        style={{
                            padding: '0.75rem 1.5rem',
                            textDecoration: 'none',
                            color: 'var(--text)',
                            fontWeight: 500,
                            borderBottom: (location.pathname === '/' || location.pathname === '/managers') ? '2px solid var(--accent)' : '2px solid transparent',
                            transition: 'all 0.2s ease'
                        }}
                    >
                        Managers
                    </Link>
                </div>
            </div>

            {/* Page Content */}
            <div>
                {children}
            </div>

            <style jsx>{`
                @media (max-width: 768px) {
                    .layout-header {
                        flex-direction: column !important;
                        padding: 1rem !important;
                        gap: 1rem !important;
                        align-items: stretch !important;
                    }

                    .layout-spacer {
                        display: none !important;
                    }

                    .layout-title {
                        font-size: 1.25rem !important;
                        text-align: center !important;
                        white-space: normal !important;
                    }

                    .layout-search-container {
                        justify-content: center !important;
                    }
                }
            `}</style>
        </div>
    );
}
