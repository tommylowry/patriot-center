import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usePlayersList } from '../hooks/usePlayersList';

export default function SearchBar() {
    const [query, setQuery] = useState('');
    const [isOpen, setIsOpen] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const searchRef = useRef(null);
    const navigate = useNavigate();
    const { players, loading } = usePlayersList();

    // Filter options (players and managers) based on query
    const filteredOptions = React.useMemo(() => {
        if (!query.trim() || loading) return [];

        const lowerQuery = query.toLowerCase();

        return players
            .filter(option => {
                const fullName = (option.full_name || option.name || '').toLowerCase();

                // For managers (no first_name/last_name), only check full_name
                if (option.type === 'manager') {
                    return fullName.startsWith(lowerQuery);
                }

                // For players, check first_name, last_name, or full_name
                const firstName = (option.first_name || '').toLowerCase();
                const lastName = (option.last_name || '').toLowerCase();

                return firstName.startsWith(lowerQuery) ||
                       lastName.startsWith(lowerQuery) ||
                       fullName.startsWith(lowerQuery);
            })
            .sort((a, b) => {
                // FIRST PRIORITY: Managers ALWAYS come before players
                const aIsManager = a.type === 'manager';
                const bIsManager = b.type === 'manager';

                if (aIsManager && !bIsManager) return -1;
                if (!aIsManager && bIsManager) return 1;

                // SECOND PRIORITY: Within same type, prioritize exact matches
                const aFullName = (a.full_name || a.name || '').toLowerCase();
                const bFullName = (b.full_name || b.name || '').toLowerCase();
                const aFirstName = (a.first_name || '').toLowerCase();
                const bFirstName = (b.first_name || '').toLowerCase();
                const aLastName = (a.last_name || '').toLowerCase();
                const bLastName = (b.last_name || '').toLowerCase();

                const aStartsWithFull = aFullName.startsWith(lowerQuery);
                const bStartsWithFull = bFullName.startsWith(lowerQuery);
                const aStartsWithFirst = aFirstName.startsWith(lowerQuery);
                const bStartsWithFirst = bFirstName.startsWith(lowerQuery);
                const aStartsWithLast = aLastName.startsWith(lowerQuery);
                const bStartsWithLast = bLastName.startsWith(lowerQuery);

                if (aStartsWithFull && !bStartsWithFull) return -1;
                if (!aStartsWithFull && bStartsWithFull) return 1;
                if (aStartsWithFirst && !bStartsWithFirst) return -1;
                if (!aStartsWithFirst && bStartsWithFirst) return 1;
                if (aStartsWithLast && !bStartsWithLast) return -1;
                if (!aStartsWithLast && bStartsWithLast) return 1;

                // THIRD PRIORITY: Sort alphabetically
                return aFullName.localeCompare(bFullName);
            })
            .slice(0, 10); // Limit to 10 results AFTER sorting
    }, [query, players, loading]);

    // Close dropdown when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (searchRef.current && !searchRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Reset selected index when filtered options change
    useEffect(() => {
        setSelectedIndex(0);
    }, [filteredOptions.length]);

    // Handle keyboard navigation
    const handleKeyDown = (e) => {
        if (!isOpen || filteredOptions.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev => Math.min(prev + 1, filteredOptions.length - 1));
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev => Math.max(prev - 1, 0));
                break;
            case 'Enter':
                e.preventDefault();
                if (filteredOptions[selectedIndex]) {
                    selectOption(filteredOptions[selectedIndex]);
                }
                break;
            case 'Escape':
                e.preventDefault();
                setIsOpen(false);
                setQuery('');
                break;
            default:
                break;
        }
    };

    const selectOption = (option) => {
        // Navigate based on type
        if (option.type === 'manager') {
            if (!option.name) return;
            navigate(`/manager/${encodeURIComponent(option.name)}`);
        } else {
            if (!option.player_id || option.provide_link === false) return;
            navigate(`/player/${option.player_id}`);
        }

        setQuery('');
        setIsOpen(false);
    };

    const handleInputChange = (e) => {
        const value = e.target.value;
        setQuery(value);
        setIsOpen(value.trim().length > 0);
    };

    const highlightMatch = (text, query) => {
        if (!query.trim()) return text;

        const lowerText = text.toLowerCase();
        const lowerQuery = query.toLowerCase();
        const index = lowerText.indexOf(lowerQuery);

        if (index === -1) return text;

        const before = text.substring(0, index);
        const match = text.substring(index, index + query.length);
        const after = text.substring(index + query.length);

        return (
            <>
                {before}
                <strong style={{ fontWeight: 700, color: 'var(--success)' }}>{match}</strong>
                {after}
            </>
        );
    };

    return (
        <div ref={searchRef} className="search-bar-wrapper" style={{ position: 'relative', width: '300px', maxWidth: '100%' }}>
            <input
                type="text"
                placeholder="Search players or managers..."
                value={query}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                onFocus={() => query.trim().length > 0 && setIsOpen(true)}
                style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    fontSize: '0.9rem',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    backgroundColor: 'var(--bg)',
                    color: 'var(--text)',
                    outline: 'none',
                    transition: 'border-color 0.2s'
                }}
                onMouseEnter={(e) => e.target.style.borderColor = 'var(--accent)'}
                onMouseLeave={(e) => !isOpen && (e.target.style.borderColor = 'var(--border)')}
            />

            {isOpen && filteredOptions.length > 0 && (
                <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    marginTop: '0.25rem',
                    backgroundColor: 'var(--bg-alt)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    maxHeight: '400px',
                    overflowY: 'auto',
                    zIndex: 1000
                }}>
                    {filteredOptions.map((option, index) => (
                        <div
                            key={option.player_id || option.name || index}
                            onClick={() => selectOption(option)}
                            onMouseEnter={() => setSelectedIndex(index)}
                            style={{
                                padding: '0.75rem 1rem',
                                cursor: 'pointer',
                                backgroundColor: index === selectedIndex ? 'var(--accent)' : 'transparent',
                                color: index === selectedIndex ? 'white' : 'var(--text)',
                                borderBottom: index < filteredOptions.length - 1 ? '1px solid var(--border)' : 'none',
                                transition: 'background-color 0.15s'
                            }}
                        >
                            <div style={{ fontWeight: 500, marginBottom: '0.15rem' }}>
                                {highlightMatch(option.full_name || option.name || '', query)}
                            </div>
                            {option.type === 'manager' ? (
                                <div style={{
                                    fontSize: '0.8rem',
                                    opacity: 0.8
                                }}>
                                    Manager
                                </div>
                            ) : (
                                option.position && (
                                    <div style={{
                                        fontSize: '0.8rem',
                                        opacity: 0.8
                                    }}>
                                        {option.position}{option.team ? ` • ${option.team}` : ''}
                                    </div>
                                )
                            )}
                        </div>
                    ))}
                </div>
            )}

            {isOpen && query.trim().length > 0 && filteredOptions.length === 0 && !loading && (
                <div style={{
                    position: 'absolute',
                    top: '100%',
                    left: 0,
                    right: 0,
                    marginTop: '0.25rem',
                    backgroundColor: 'var(--bg-alt)',
                    border: '1px solid var(--border)',
                    borderRadius: '6px',
                    padding: '1rem',
                    color: 'var(--muted)',
                    textAlign: 'center',
                    zIndex: 1000
                }}>
                    No results found
                </div>
            )}

            <style jsx>{`
                @media (max-width: 768px) {
                    .search-bar-wrapper {
                        width: 100% !important;
                    }
                }
            `}</style>
        </div>
    );
}
