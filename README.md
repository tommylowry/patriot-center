# Patriot Center

A comprehensive fantasy football analytics platform that calculates and displays advanced metrics for a private fantasy football league across multiple seasons (2019-2025).

## Overview

Patriot Center tracks 16 managers in a multi-year fantasy football league and provides detailed insights into player performance using **ffWAR (Fantasy Football Wins Above Replacement)** - a custom metric that measures how many wins a player adds compared to a "replacement level" player.

## Key Features

- **Advanced Metrics**: Calculate ffWAR by simulating hypothetical matchups with positional replacement averages
- **Multi-Season Analytics**: Historical tracking across 7+ seasons (2019-2025)
- **Flexible Filtering**: Filter by season, week, manager, or position
- **Player Detail Pages**: In-depth statistics and manager history for each player
- **Real-time Data**: Integration with Sleeper fantasy football API
- **Performance Optimized**: Local JSON caching to minimize API calls

## Technology Stack

### Frontend
- React 19.2.0 with React Router
- Deployed on Netlify
- Built with react-scripts

### Backend
- **Framework**: Python Flask with CORS support
- **Server**: Gunicorn WSGI server with nginx reverse proxy
- **Deployment**: Oracle Cloud Infrastructure (Always Free Tier)
- **Architecture**:
  - Service layer for business logic (aggregations, filtering, validation)
  - Utility layer for data loading and caching
  - Incremental cache updates to minimize API calls
  - JSON file-based caching system with progress markers

### Data Sources
- **Sleeper API**: Real-time fantasy football data (rosters, matchups, player stats)
- **Calculated Metrics**:
  - ffWAR (Fantasy Football Wins Above Replacement)
  - Replacement-level scores (3-year rolling averages)
  - Aggregated player/manager statistics
- **Caching Strategy**: Local JSON caches with incremental updates and resumability

## Project Structure

```
.
├── patriot_center_frontend/    # React frontend
│   ├── src/                    # React source code
│   │   ├── components/         # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API service layer
│   │   └── App.js             # Main application
│   ├── public/                # Static assets
│   ├── build/                 # Production build output
│   └── package.json           # Frontend dependencies
│
├── patriot_center_backend/    # Python Flask backend
│   ├── app.py                 # Main Flask application and route handlers
│   ├── constants.py           # Configuration (league IDs, file paths, team data)
│   │
│   ├── services/              # Business logic layer
│   │   ├── managers.py        # Starters data filtering and queries
│   │   ├── aggregated_data.py # Player/manager aggregation logic
│   │   ├── players.py         # Player cache access
│   │   └── valid_options.py   # Dynamic filter validation service
│   │
│   ├── utils/                 # Data loading and caching utilities
│   │   ├── cache_utils.py     # Generic cache load/save operations
│   │   ├── sleeper_api_handler.py  # Sleeper API client
│   │   ├── starters_loader.py      # Weekly roster data loader
│   │   ├── ffWAR_loader.py         # ffWAR computation and caching
│   │   ├── replacement_score_loader.py  # Replacement-level calculations
│   │   ├── player_ids_loader.py    # Player metadata management
│   │   └── update_all_caches.py    # Batch cache update orchestrator
│   │
│   ├── data/                  # JSON cache files (auto-generated)
│   │   ├── starters_cache.json          # Weekly starter rosters
│   │   ├── ffWAR_cache.json             # Computed ffWAR values
│   │   ├── replacement_score_cache.json # Positional baselines
│   │   ├── players_cache.json           # Player metadata
│   │   └── valid_options_cache.json     # Filter validation data
│   │
│   └── tests/                 # Unit and integration tests
│       ├── test_app.py        # API endpoint tests
│       ├── services/          # Service layer tests
│       └── utils/             # Utility function tests
│
├── deployment/                # Deployment scripts and guides
│   ├── oracle_deploy.sh       # Oracle Cloud setup script
│   ├── upload_to_oracle.sh    # File upload helper
│   ├── ORACLE_DEPLOYMENT_GUIDE.md  # Deployment docs
│   └── GITHUB_SECRETS_SETUP.md     # GitHub Actions setup
├── Dockerfile                 # Docker configuration
└── requirements.txt           # Backend dependencies
```

## API Endpoints

All endpoints support flexible positional parameters that are automatically parsed:
- Numeric values matching league years (2019-2025) are interpreted as seasons
- Numeric values 1-17 are interpreted as weeks
- String values matching manager names are interpreted as manager filters
- String values matching player names are interpreted as player filters

### Core Data Endpoints

#### Starters Data
```
GET /get_starters[/<year>][/<week>][/<manager>]
```
Returns weekly starter rosters with points scored and position information.
- Supports any combination of year, week, and manager filters
- Query param `format=json` returns nested structure (default is flattened records)

#### Aggregated Player Stats
```
GET /get_aggregated_players[/<year>][/<week>][/<manager>]
```
Returns aggregated player statistics (total points, games started, ffWAR) for a manager.
- Aggregates across all weeks/seasons matching the filters
- Includes player images, positions, and teams

#### Aggregated Manager Stats
```
GET /get_aggregated_managers/<player>[/<year>][/<week>]
```
Returns aggregated statistics showing which managers have used a specific player.
- Player name in URL (use underscores for spaces, %27 for apostrophes)
- Shows total points, games started, and ffWAR per manager

#### Player-Manager Aggregation
```
GET /get_player_manager_aggregation/<player>/<manager>[/<year>][/<week>]
```
Returns statistics for a specific player-manager pairing.

#### Player List
```
GET /players/list
```
Returns metadata for all players in the system (names, positions, teams, slugs).

### Filter Validation
```
GET /valid_options[/<arg1>][/<arg2>][/<arg3>][/<arg4>]
```
Dynamic endpoint that returns valid filter options based on current selections.
- Accepts up to 4 filter arguments (year, week, manager, player, position)
- Returns available options that have data for the selected filters
- Used by frontend to populate dropdown menus

### Health & Status
```
GET /        # Service info and endpoint list
GET /health  # Health check (returns {"status": "healthy"})
GET /ping    # Liveness check (returns "pong")
```

## Development Setup

### Frontend

```bash
cd patriot_center_frontend

# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

### Backend

```bash
# Create virtual environment (from project root)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server (from project root)
python -m patriot_center_backend.app
```

## Deployment

### Frontend (Netlify)
The frontend is automatically deployed to Netlify at [patriotcenter.netlify.app](https://patriotcenter.netlify.app)

Deployment is triggered automatically on push to `main` branch via Netlify's GitHub integration.

### Backend (Oracle Cloud)
The backend API is deployed on Oracle Cloud Infrastructure's Always Free Tier at `https://patriot-center.duckdns.org`

**Initial Setup:**
See [deployment/ORACLE_DEPLOYMENT_GUIDE.md](deployment/ORACLE_DEPLOYMENT_GUIDE.md) for complete deployment instructions.

**Auto-Deployment:**
Pushes to `main` branch automatically deploy the backend via GitHub Actions, which:
- SSHs into the Oracle Cloud instance
- Pulls the latest code
- Restarts the backend service

**Manual Deployment:**
```bash
ssh ubuntu@<oracle-ip>
cd /opt/patriot-center
git pull
sudo systemctl restart patriot-center
```

## Testing

```bash
# Run from project root
pytest
pytest --cov  # Run with coverage
```

## How ffWAR Works

ffWAR (Fantasy Football Wins Above Replacement) measures a player's value by:

1. Taking each game where a player was started
2. Simulating what would have happened if a "replacement level" player (positional average) was started instead
3. Calculating the net change in wins/losses
4. Aggregating across all weeks to determine total wins contributed

This provides a more nuanced view of player value than raw points alone.

## Backend Architecture

### Caching Strategy

The backend uses an incremental JSON caching system to minimize API calls and computation:

1. **Progress Markers**: Each cache tracks `Last_Updated_Season` and `Last_Updated_Week`
2. **Resumability**: Updates can be interrupted and resumed without losing progress
3. **Incremental Updates**: Only fetches/computes data for new weeks since last update
4. **Import-time Loading**: Caches are loaded when modules are imported for fast access

### Cache Dependencies

The caching system has a specific order of operations:

```
1. player_ids_cache.json      (Sleeper API: player metadata, refreshed weekly)
   ↓
2. starters_cache.json         (Sleeper API: weekly rosters + matchups)
   ↓
3. replacement_score_cache.json (Computed: positional replacement levels)
   ↓
4. ffWAR_cache.json            (Computed: wins above replacement via simulations)
   ↓
5. valid_options_cache.json    (Derived: available filter combinations)
```

### Data Flow

```
Sleeper API
    ↓
player_ids_loader → player_ids.json
    ↓
starters_loader → starters_cache.json + valid_options_cache.json
    ↓
replacement_score_loader → replacement_score_cache.json
    ↓
ffWAR_loader → ffWAR_cache.json
    ↓
aggregated_data service → Aggregated responses
```

### Key Design Patterns

- **Service Layer**: Business logic separated from Flask routes (services/)
- **Utility Layer**: Reusable data loading and caching logic (utils/)
- **Constants Module**: Centralized configuration (league IDs, file paths, team data)
- **Positional Arguments**: Flexible URL parsing allows filter arguments in any order
- **Response Formats**: Dual format support (nested JSON vs flattened records)

## League Information

- **Number of Managers**: 16
- **Seasons Tracked**: 2019-2025
- **Regular Season Weeks**: 1-17
- **Positions**: QB, RB, WR, TE, K, DEF

## License

Private project for Patriot Center fantasy football league.
