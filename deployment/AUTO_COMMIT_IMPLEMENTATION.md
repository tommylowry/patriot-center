# Automated Cache Commit Implementation

## Summary

The Patriot Center backend now supports automatic git commits and pushes when cache files are updated. This ensures cache updates on the production server are automatically synchronized with the GitHub repository.

## What Was Implemented

### 1. Git Auto-Commit Utility (`patriot_center_backend/utils/git_auto_commit.py`)

A new utility module that handles:
- Detecting changes in the `data/` directory
- Creating feature branches with date stamps
- Committing with bot identity
- Pushing to GitHub and merging to main
- Proper error handling and logging

**Key Functions:**
- `has_cache_changes()` - Checks if cache files have uncommitted changes
- `commit_and_push_cache_updates()` - Performs the full commit/push workflow
- `setup_git_credentials()` - Verifies git authentication is configured

**Bot Identity:**
- Name: `Patriot Center Bot`
- Email: `bot@patriotcenter.local`

### 2. Modified `update_all_caches.py`

Enhanced the cache update orchestrator to:
- Accept an `auto_commit` parameter
- Read from `PATRIOT_AUTO_COMMIT_CACHE` environment variable
- Call the git auto-commit utility after cache updates
- Provide clear logging of commit status

**Usage:**
```python
# Auto-commit enabled
update_all_caches(auto_commit=True)

# Auto-commit disabled (local development)
update_all_caches(auto_commit=False)

# Use environment variable (production)
update_all_caches()  # Reads PATRIOT_AUTO_COMMIT_CACHE
```

### 3. Setup Guide (`deployment/GIT_AUTO_COMMIT_SETUP.md`)

Comprehensive documentation covering:
- Two authentication options (SSH keys or PAT)
- Step-by-step setup instructions
- Testing procedures
- Troubleshooting common issues
- Security considerations
- How to enable/disable auto-commit

### 4. Updated `.gitignore`

Added security entries to prevent accidental commits of:
- `.git-credentials`
- SSH private keys (`*.pem`, `id_rsa`, `id_ed25519`)
- PuTTY keys (`*.ppk`)

## How It Works

### Normal Cache Update Flow

```
Cache Update Triggered
         ↓
update_all_caches() called
         ↓
Caches updated on disk
         ↓
commit_and_push_cache_updates() called
         ↓
1. Create branch: cache-update-MM-DD-YY
2. Stage changes: git add patriot_center_backend/data/
3. Commit: "Update cache data (timestamp)"
4. Push branch to GitHub
5. Merge branch into main
6. Push main to GitHub
         ↓
GitHub Actions (oracle-deploy.yml) triggered
         ↓
Server pulls latest changes
         ↓
Service restarts with updated cache
```

### Environment Control

**Production (Oracle Server):**
```bash
# Set in systemd service file
Environment="PATRIOT_AUTO_COMMIT_CACHE=true"
```

**Local Development:**
```bash
# Don't set the variable, or explicitly disable
export PATRIOT_AUTO_COMMIT_CACHE=false
```

## Authentication Setup Required

Before this will work on the Oracle server, you need to set up git authentication. Choose one:

### Option 1: SSH Keys (Recommended)
1. Generate SSH key pair
2. Add public key to GitHub
3. Copy private key to Oracle server
4. Update git remote to use SSH URL

### Option 2: Personal Access Token
1. Create PAT on GitHub with `repo` scope
2. Configure credential helper on server
3. Store credentials securely
4. Update git remote to use HTTPS URL

**See [GIT_AUTO_COMMIT_SETUP.md](./GIT_AUTO_COMMIT_SETUP.md) for detailed instructions.**

## Testing Locally

You can test the git utility locally (without actually pushing):

```bash
cd /path/to/patriot-center

# Test credential check
python -c "from patriot_center_backend.utils.git_auto_commit import setup_git_credentials; setup_git_credentials()"

# Test change detection
python -c "from patriot_center_backend.utils.git_auto_commit import has_cache_changes; print(has_cache_changes())"

# Test full workflow (WARNING: will actually commit and push!)
# Uncomment the last line in git_auto_commit.py first
python -m patriot_center_backend.utils.git_auto_commit
```

## Security Features

1. **Bot Identity**: All automated commits clearly marked
2. **Credential Protection**: Sensitive files in .gitignore
3. **Environment Control**: Easy to enable/disable per environment
4. **Branch Strategy**: Creates feature branches before merging
5. **Error Handling**: Won't crash if git operations fail

## Deployment Checklist

When deploying to production:

- [ ] Set up SSH keys or PAT authentication
- [ ] Test git operations manually on server
- [ ] Add `PATRIOT_AUTO_COMMIT_CACHE=true` to systemd service
- [ ] Reload systemd and restart service
- [ ] Trigger a test cache update
- [ ] Verify commit appears on GitHub
- [ ] Verify oracle-deploy.yml workflow runs
- [ ] Check that server pulled the changes

## Maintenance

### Monitoring

Check logs to see if auto-commits are working:
```bash
sudo journalctl -u patriot-center -f | grep "auto-commit"
```

### Disabling

Temporarily disable without code changes:
```bash
sudo nano /etc/systemd/system/patriot-center.service
# Comment out: Environment="PATRIOT_AUTO_COMMIT_CACHE=true"
sudo systemctl daemon-reload
sudo systemctl restart patriot-center
```

### Manual Cache Updates

If you need to update caches without triggering auto-commit:
```bash
python -c "from patriot_center_backend.utils.update_all_caches import update_all_caches; update_all_caches(auto_commit=False)"
```

## Future Enhancements

Possible improvements for the future:

1. **Slack/Email Notifications**: Alert when cache updates are committed
2. **Conflict Resolution**: Handle merge conflicts automatically
3. **Rate Limiting**: Prevent too many commits in a short time
4. **Rollback Support**: Quick rollback if cache update causes issues
5. **Webhook Integration**: Trigger updates via GitHub webhook
6. **PR Creation**: Create PRs instead of direct merges for review

## Files Modified/Created

**New Files:**
- `patriot_center_backend/utils/git_auto_commit.py`
- `deployment/GIT_AUTO_COMMIT_SETUP.md`
- `deployment/AUTO_COMMIT_IMPLEMENTATION.md` (this file)

**Modified Files:**
- `patriot_center_backend/utils/update_all_caches.py`
- `.gitignore`

## Questions?

Refer to [GIT_AUTO_COMMIT_SETUP.md](./GIT_AUTO_COMMIT_SETUP.md) for detailed setup instructions and troubleshooting.
