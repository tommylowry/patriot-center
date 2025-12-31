import React, { useState, useEffect, useRef } from 'react';
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
    const [isHeaderVisible, setIsHeaderVisible] = useState(true);
    const lastScrollY = useRef(0);
    const ticking = useRef(false);

    useEffect(() => {
        const handleScroll = () => {
            if (!ticking.current) {
                window.requestAnimationFrame(() => {
                    const currentScrollY = window.scrollY;

                    // Only apply scroll behavior if we've scrolled past 50px from top
                    if (currentScrollY > 50) {
                        if (currentScrollY > lastScrollY.current) {
                            // Scrolling down - hide header
                            setIsHeaderVisible(false);
                        } else {
                            // Scrolling up - show header
                            setIsHeaderVisible(true);
                        }
                    } else {
                        // Always show header when near top of page
                        setIsHeaderVisible(true);
                    }

                    lastScrollY.current = currentScrollY;
                    ticking.current = false;
                });

                ticking.current = true;
            }
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    return (
        <div style={{ position: 'relative', minHeight: '100vh' }}>
            {/* Header with Title and Search Bar */}
            <div className="layout-header" style={{
                position: 'sticky',
                top: 0,
                zIndex: 100,
                backgroundColor: 'var(--bg)',
                borderBottom: '1px solid var(--border)',
                paddingBottom: 0,
                transform: isHeaderVisible ? 'translateY(0)' : 'translateY(-100%)',
                transition: 'transform 0.3s ease-in-out'
            }}>
                {/* Title and Search Row */}
                <div className="title-search-row" style={{
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
                    {/* Search Bar on Right (Desktop) */}
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }} className="layout-search-container-desktop">
                        <SearchBar />
                    </div>
                </div>

                {/* Search Bar Below Title (Mobile Only) */}
                <div className="layout-search-container-mobile" style={{ display: 'none' }}>
                    <SearchBar />
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
                    .title-search-row {
                        padding: 0.75rem 1rem !important;
                        justify-content: center !important;
                    }

                    .layout-spacer {
                        display: none !important;
                    }

                    .layout-title {
                        font-size: 1.25rem !important;
                        text-align: center !important;
                        white-space: normal !important;
                    }

                    .layout-search-container-desktop {
                        display: none !important;
                    }

                    .layout-search-container-mobile {
                        display: block !important;
                        padding: 0 1rem 0.75rem 1rem;
                        width: 100%;
                    }

                    .nav-tabs {
                        padding: 0 1rem !important;
                    }
                }
            `}</style>
        </div>
    );
}
