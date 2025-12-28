# Cache Update System Changes

## Summary of Changes

Migrated from server-side cache updates with `Last_Updated` metadata to GitHub Actions with file modification time tracking.

## What Changed

### 1. GitHub Actions Workflow Schedule
- **File**: [.github/workflows/update-cache.yml](../.github/workflows/update-cache.yml)
- **Schedule**: Changed from daily 7:30 PM EST to **every Monday at 3:00 AM EST**
- **Cron**: `0 8 * * 1` (08:00 UTC = 3:00 AM EST on Mondays)
- **Cannot be manually triggered** (no `workflow_dispatch` event)

### 2. Removed `Last_Updated` Field from Cache Files
- **File**: `player_ids.json`
- **Change**: Removed `Last_Updated` timestamp field
- **Reason**: Git commit timestamps now track when files were updated

### 3. Updated `player_ids_loader.py` Logic
- **File**: [patriot_center_backend/utils/player_ids_loader.py](../patriot_center_backend/utils/player_ids_loader.py)
- **Change**: Now uses **file modification time** instead of `Last_Updated` field
- **Benefit**: Prevents expensive Sleeper API calls if file was modified <1 week ago

**How it works now:**
```python
# Check file modification time
file_mtime = os.path.getmtime(PLAYER_IDS_CACHE_FILE)
file_age = datetime.now() - datetime.fromtimestamp(file_mtime)

# If file is fresh (<1 week old), reuse cache
if file_age < timedelta(weeks=1):
    # Return cached data without API call

# Otherwise, call expensive Sleeper API to refresh
```

### 4. Other Cache Loaders Already Clean
- **Files**: `starters_loader.py`, `player_data_loader.py`, `replacement_score_loader.py`
- **Status**: Already remove `Last_Updated_Season` and `Last_Updated_Week` before saving
- **No changes needed**: These were already not committing metadata fields

### 5. Updated Tests
- **File**: [tests/utils/test_player_ids_loader.py](../patriot_center_backend/tests/utils/test_player_ids_loader.py)
- **Changes**:
  - Removed references to `Last_Updated` field
  - Updated tests to use file mtime approach
  - All 12 tests passing ✅

## Benefits

### 1. Cleaner Version Control
- Cache files no longer contain metadata fields
- Git commit messages show when files were updated
- Diffs are cleaner (no `Last_Updated` noise)

### 2. Protected Expensive API Calls
- `player_ids` data from Sleeper API only refreshed if file >1 week old
- File mtime check happens before reading JSON (faster)
- No API calls on weekly GitHub Actions runs unless data is stale

### 3. Secure Automation
- Cannot be manually triggered (schedule-only)
- Runs every Tuesday at 1 AM automatically
- No HTTP endpoint to exploit

## How the System Works Now

### Weekly Update Flow (Every Tuesday 1 AM EST):

```
1. GitHub Actions triggers scheduled workflow
2. Checks out repository
3. Runs:
  a) update_starters_cache()
  b) update_replacement_score_cache()
  c) update_player_data_cache()
  d) update_player_ids()

   For player_ids:
   - Check file mtime
   - If <1 week old: reuse cache (no API call)
   - If >1 week old: fetch from Sleeper API

   For other caches:
   - Always update with latest data

4. Commit changes if files modified
5. Push to main branch
6. oracle-deploy.yml triggers
7. Oracle server pulls latest changes
```

### File Modification Time Tracking:

When GitHub Actions commits a file:
- File gets new modification time
- Next run checks mtime
- If <1 week old, skips API call
- If >1 week old (or missing), fetches fresh data

## Testing Locally

You can test the cache update logic locally:

```bash
cd patriot_center_backend

# Test player_ids loader (won't call API if file is <1 week old)
python -c "from utils.player_ids_loader import load_player_ids; load_player_ids()"

# Run tests
pytest tests/utils/test_player_ids_loader.py -v
```

## Force Refresh Player IDs

If you need to force a refresh of the expensive player_ids data:

```bash
# Option 1: Delete the cache file
rm patriot_center_backend/data/player_ids.json

# Option 2: "Touch" the file to set mtime to 2 weeks ago
touch -t $(date -v-14d '+%Y%m%d%H%M') patriot_center_backend/data/player_ids.json

# Then run the loader
cd patriot_center_backend
python -c "from utils.player_ids_loader import load_player_ids; load_player_ids()"
```

## Notes

- **player_ids.json** will only be updated if it's >1 week old (expensive API protection)
- **Other cache files** are updated every Monday regardless (not expensive)
- **No manual triggers** - workflow only runs on schedule
- **Git commits** track all cache updates with timestamps
- **File mtime** determines cache freshness, not JSON metadata
