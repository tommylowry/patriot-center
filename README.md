# Patriot Center

A fantasy football analytics platform that calculates and displays advanced metrics for a private fantasy football league across multiple seasons (2019-2025).

## Overview

Patriot Center tracks 16 managers in a multi-year fantasy football league and provides detailed insights into player performance using **ffWAR (Fantasy Football Wins Above Replacement)** - a custom metric that measures how many wins a player adds compared to a "replacement level" player.

## Key Features

- **Advanced Metrics**: Calculate ffWAR by simulating hypothetical matchups with positional replacement averages
- **Multi-Season Analytics**: Historical tracking across 7 seasons (2019-2025)
- **Manager Profiles**: Summary stats, head-to-head records, transaction history, and awards
- **Player Detail Pages**: In-depth statistics and manager history for each player
- **Dynamic Filtering**: Filter by season, week, manager, or position with context-aware dropdowns
- **Head-to-Head Comparisons**: Matchup history and trade history between any two managers
- **Real-time Data**: Integration with Sleeper fantasy football API
- **Session-Scoped API Caching**: In-memory response cache on Sleeper API calls to minimize redundant requests during cache updates

## Technology Stack

### Frontend
- React 19.2 with React Router 7
- Deployed on Netlify
- Custom hooks for data fetching
- Context-based loading state management

### Backend
- **Framework**: Python Flask with blueprinted route organization
- **Server**: Gunicorn WSGI server with nginx reverse proxy
- **Deployment**: Oracle Cloud Infrastructure (Always Free Tier)
- **Architecture**:
  - **Routes** - Flask blueprints for API endpoint registration
  - **Exporters** - Transform cached data into API response format
  - **Cache Queries** - Read-only access to cached data with filtering
  - **Cache Updaters** - Refresh caches from Sleeper API with progress tracking
  - **Cache Manager** - Central singleton for all cache operations and persistence
  - JSON file-based caching with incremental updates and resumability

### Data Sources
- **Sleeper API**: Fantasy football data (rosters, matchups, player stats, transactions)
- **Calculated Metrics**:
  - ffWAR (Fantasy Football Wins Above Replacement)
  - Replacement-level scores (3-year rolling averages)
  - Aggregated player/manager statistics

## Project Structure

```
.
├── patriot_center_frontend/        # React frontend
│   ├── src/
│   │   ├── pages/                  # ManagersPage, ManagerPage, PlayerPage,
│   │   │                           #   HeadToHeadPage, MatchupPage
│   │   ├── components/             # Layout, PlayerRow, MatchupCard,
│   │   │                           #   TradeCard, WaiverCard, FilterDropdown
│   │   ├── hooks/                  # useAggregatedPlayers, useManagerSummary,
│   │   │                           #   useHeadToHead, useDynamicFiltering, etc.
│   │   ├── contexts/               # LoadingContext
│   │   ├── config/                 # API endpoint configuration
│   │   └── services/               # Options/constants
│   └── package.json
│
├── patriot_center_backend/         # Python Flask backend
│   ├── app.py                      # Flask app with blueprint registration
│   ├── constants.py                # League IDs, manager mappings, team data
│   │
│   ├── routes/                     # Flask blueprints
│   │   ├── health.py               # /, /ping, /health
│   │   ├── aggregation.py          # /get_aggregated_players, /get_aggregated_managers
│   │   ├── managers.py             # /api/managers/<name>/summary, head-to-head, etc.
│   │   ├── options.py              # /options/list, /dynamic_filtering
│   │   └── starters.py             # /get_starters
│   │
│   ├── exporters/                  # Response formatters
│   │   ├── aggregation_exporter.py
│   │   ├── award_exporter.py
│   │   ├── head_to_head_exporter.py
│   │   ├── summary_exporter.py
│   │   ├── transaction_exporter.py
│   │   └── ...
│   │
│   ├── cache/
│   │   ├── cache_manager.py        # Central cache singleton
│   │   ├── cache_updater.py        # Orchestrates update order
│   │   ├── queries/                # Read-only cache access
│   │   │   ├── aggregation_queries.py
│   │   │   ├── head_to_head_queries.py
│   │   │   ├── manager_queries.py
│   │   │   ├── starters_queries.py
│   │   │   └── ...
│   │   ├── updaters/               # Cache refresh from Sleeper API
│   │   │   ├── starters_updater.py
│   │   │   ├── player_data_updater.py
│   │   │   ├── weekly_data_updater.py
│   │   │   └── processors/         # Transaction processing
│   │   │       └── transactions/
│   │   └── cached_data/            # JSON cache files (auto-generated)
│   │
│   ├── calculations/               # Statistical calculations
│   │   ├── ffwar_calculator.py
│   │   ├── player_score_calculator.py
│   │   └── rolling_average_calculator.py
│   │
│   ├── players/                    # Player data handling
│   │   ├── player_data.py
│   │   └── player_scores_fetcher.py
│   │
│   ├── dynamic_filtering/          # Context-aware filter logic
│   │   ├── dynamic_filter.py
│   │   ├── find_valid_options.py
│   │   └── validator.py
│   │
│   ├── utils/                      # Shared utilities
│   │   ├── sleeper_api.py          # SleeperApiClient singleton with response cache
│   │   ├── sleeper_helpers.py      # Sleeper API helper functions
│   │   ├── image_url_handler.py    # Manager avatar URL management
│   │   ├── argument_parser.py      # Flexible URL argument parsing
│   │   ├── data_formatters.py      # Dict flattening, record conversion
│   │   └── helpers.py              # Player ID/name lookups
│   │
│   └── tests/                      # Unit tests (mirrors source structure)
│       ├── cache/
│       │   ├── queries/
│       │   └── updaters/
│       │       └── processors/transactions/
│       ├── calculations/
│       ├── dynamic_filtering/
│       ├── exporters/
│       ├── players/
│       └── utils/
│
├── .github/workflows/
│   ├── backend-tests.yml           # PR/push: run pytest with coverage
│   ├── oracle-deploy.yml           # Push to main: deploy backend to Oracle Cloud
│   └── update-cache.yml            # Weekly cron: update caches and deploy
│
├── requirements.txt                # Backend dependencies
├── pytest.ini                      # Pytest configuration
├── netlify.toml                    # Netlify frontend deployment config
└── pyproject.toml                  # Ruff and Pyright configuration
                                    #   (in patriot_center_backend/)
```

## API Endpoints

All endpoints support flexible positional parameters that are automatically parsed:
- Numeric values matching league years (2019-2025) are interpreted as seasons
- Numeric values 1-17 are interpreted as weeks
- String values matching manager names are interpreted as manager filters

### Health & Status
```
GET /        # Service info
GET /ping    # Liveness check (returns "pong")
GET /health  # Health check (returns {"status": "healthy"})
```

### Starters
```
GET /get_starters[/<year>][/<week>][/<manager>]
```
Returns weekly starter rosters with points scored and position information.
- Query param `format=json` returns nested structure (default is flattened records)

### Aggregated Data
```
GET /get_aggregated_players[/<year>][/<week>][/<manager>]
GET /get_aggregated_managers/<player>[/<year>][/<week>]
GET /get_player_manager_aggregation/<player>/<manager>[/<year>][/<week>]
```

### Manager Endpoints
```
GET /get/managers/list/<true|false>
GET /api/managers/<name>/summary[/<year>]
GET /api/managers/<name>/head-to-head/<opponent>[/<year>]
GET /api/managers/<name>/transactions[/<year>]
GET /api/managers/<name>/awards
```

### Options & Filtering
```
GET /options/list
GET /dynamic_filtering?yr=&wk=&mgr=&pos=&plyr=
```
Dynamic endpoint that returns valid filter options based on current selections.

## Development Setup

### Frontend

```bash
cd patriot_center_frontend
npm ci
npm start
```

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m patriot_center_backend.app
```

## CI/CD

- **Backend Tests**: Run on PRs and pushes to main when backend files change
- **Oracle Deploy**: Automatically deploys backend on push to main
- **Cache Update**: Scheduled weekly (Tuesday 1:00 AM EST) - updates all caches from Sleeper API and deploys if changes are found

## Testing

```bash
pytest                # Run all tests
pytest --cov          # Run with coverage
```

## How ffWAR Works

ffWAR (Fantasy Football Wins Above Replacement) measures a player's value by:

1. **Calculate scores for all NFL players** who played that week (not just rostered players)
2. **Simulate hypothetical matchups** - pair every player with every manager combination
3. **Compare vs replacement level** - determine if the player wins/loses compared to a replacement-level player at their position
4. **Aggregate net wins** - sum up the win differential across all simulated matchups
5. **Normalize and scale** - divide by total simulations, apply playoff scaling

Replacement-level scores use 3-year rolling averages by position.

## League Information

- **Managers**: 16
- **Seasons**: 2019-2025
- **Regular Season Weeks**: 1-17
- **Positions**: QB, RB, WR, TE, K, DEF

## Linting

- **Ruff**: Primary linter for style, imports, naming, and docstring conventions (Google style)
- **Flake8 + Darglint**: Supplementary checks for indentation (E1xx) and docstring-to-signature validation (DAR rules)
- **Pyright**: Static type checking

## License

Private project for Patriot Center fantasy football league.
