import React from 'react';
import SearchBar from './SearchBar';

export default function Layout({ children }) {
    return (
        <div style={{ position: 'relative', minHeight: '100vh' }}>
            {/* Header with Search Bar */}
            <div style={{
                position: 'sticky',
                top: 0,
                zIndex: 100,
                backgroundColor: 'var(--bg)',
                borderBottom: '1px solid var(--border)',
                padding: '1rem 2rem',
                display: 'flex',
                justifyContent: 'flex-end',
                alignItems: 'center'
            }}>
                <SearchBar />
            </div>

            {/* Page Content */}
            <div>
                {children}
            </div>
        </div>
    );
}
