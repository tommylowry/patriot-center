# Git Auto-Commit Setup Guide

This guide explains how to set up automated git commits for cache updates on the production Oracle server.

## Overview

When cache files are updated on the production server, the system can automatically:
1. Detect changes in `patriot_center_backend/data/`
2. Create a new branch named `cache-update-MM-DD-YY`
3. Commit the changes with bot identity
4. Push to GitHub and merge into main
5. The existing oracle-deploy.yml workflow then pulls the changes

## Prerequisites

You need to configure git authentication on the Oracle server to push to GitHub.

### Option 1: SSH Keys (Recommended)

SSH keys are more secure and don't expire like Personal Access Tokens.

**On your local machine:**
```bash
# Generate a new SSH key (if you don't have one for the server)
ssh-keygen -t ed25519 -C "oracle-patriot-center" -f ~/.ssh/oracle_patriot_center
```

**Add the public key to GitHub:**
1. Copy the public key: `cat ~/.ssh/oracle_patriot_center.pub`
2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
3. Paste the public key and save

**On the Oracle server:**
```bash
# SSH into the server
ssh ubuntu@129.80.188.14

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Copy the private key to the server
# (You can use scp from your local machine or paste it manually)
nano ~/.ssh/id_ed25519
# Paste the private key content
chmod 600 ~/.ssh/id_ed25519

# Add GitHub to known hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts

# Test the connection
ssh -T git@github.com
# Should see: "Hi [username]! You've successfully authenticated..."
```

**Update git remote to use SSH:**
```bash
cd /opt/patriot-center
git remote set-url origin git@github.com:tommylowry/patriot-center.git
```

### Option 2: Personal Access Token (PAT)

If you prefer HTTPS with a Personal Access Token:

**Create a PAT on GitHub:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope (full control of private repositories)
3. Copy the token (you won't be able to see it again!)

**On the Oracle server:**
```bash
# Configure git to use credential helper
git config --global credential.helper store

# Clone or pull once with the token to save credentials
cd /opt/patriot-center
git pull https://YOUR_TOKEN@github.com/tommylowry/patriot-center.git

# Or manually create the credentials file
echo "https://YOUR_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

**Update git remote to use HTTPS:**
```bash
cd /opt/patriot-center
git remote set-url origin https://github.com/tommylowry/patriot-center.git
```

## Enable Auto-Commit

**On the Oracle server:**

1. Set the environment variable in the systemd service:

```bash
sudo nano /etc/systemd/system/patriot-center.service
```

Add this line in the `[Service]` section:
```ini
Environment="PATRIOT_AUTO_COMMIT_CACHE=true"
```

2. Configure git identity (if not already set):

```bash
cd /opt/patriot-center
git config user.name "Patriot Center Bot"
git config user.email "bot@patriotcenter.local"
```

3. Reload and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart patriot-center
```

## Testing

You can test the auto-commit functionality manually:

```bash
cd /opt/patriot-center
source venv/bin/activate

# Test with environment variable
export PATRIOT_AUTO_COMMIT_CACHE=true
python -m patriot_center_backend.utils.update_all_caches

# Or test the git utility directly
python -m patriot_center_backend.utils.git_auto_commit
```

## How It Works

### Cache Update Flow

1. **Cache Update Triggered** (e.g., weekly cron job or API call)
   ```
   update_all_caches() is called
   ```

2. **Caches Update**
   ```
   starters_cache.json updated
   replacement_score_cache.json updated
   ffWAR_cache.json updated
   ```

3. **Auto-Commit (if enabled)**
   ```python
   commit_and_push_cache_updates()
   # Creates branch: cache-update-12-11-24
   # Commits: "Update cache data (2024-12-11 15:30:00)"
   # Pushes to GitHub
   # Merges into main
   ```

4. **GitHub Actions Triggered**
   ```
   oracle-deploy.yml detects push to main
   SSHs into Oracle server
   Runs: git reset --hard origin/main
   Restarts backend service
   ```

5. **Server Now Has Latest Cache**
   ```
   Backend serving updated cache data
   ```

### Branch Naming

Branches are named with format: `cache-update-MM-DD-YY`
- Example: `cache-update-12-11-24` for December 11, 2024
- If multiple updates happen on the same day, the branch is reused

### Commit Messages

Commits follow this format:
```
Update cache data (2024-12-11 15:30:00)

Automated cache update from production server.
```

### Bot Identity

All automated commits are made by:
- **Name**: Patriot Center Bot
- **Email**: bot@patriotcenter.local

This clearly distinguishes automated commits from manual developer commits in git history.

## Scheduling Cache Updates

You can set up a cron job to automatically update caches weekly:

```bash
sudo crontab -e
```

Add this line to run every Monday at 2 AM:
```cron
0 2 * * 1 cd /opt/patriot-center && /opt/patriot-center/venv/bin/python -m patriot_center_backend.utils.update_all_caches >> /var/log/cache-update.log 2>&1
```

## Troubleshooting

### "Permission denied (publickey)" Error

This means SSH authentication isn't working. Verify:
1. SSH key is added to GitHub
2. Private key is on the server at `~/.ssh/id_ed25519`
3. Private key has correct permissions (600)
4. Test with: `ssh -T git@github.com`

### "Authentication failed" Error (HTTPS)

This means your PAT isn't configured correctly. Verify:
1. PAT has `repo` scope
2. PAT is saved in `~/.git-credentials`
3. Remote URL uses HTTPS: `git remote -v`

### "Not in a git repository" Error

The script must run from within the git repository:
```bash
cd /opt/patriot-center
python -m patriot_center_backend.utils.update_all_caches
```

### Commits Not Appearing

Check that the environment variable is set:
```bash
echo $PATRIOT_AUTO_COMMIT_CACHE
# Should output: true
```

View logs to see if auto-commit is being triggered:
```bash
sudo journalctl -u patriot-center -f
```

## Disabling Auto-Commit

To disable auto-commit (e.g., for local development):

**Option 1: Don't set the environment variable**
```bash
# Auto-commit defaults to false if not set
python -m patriot_center_backend.utils.update_all_caches
```

**Option 2: Explicitly disable**
```bash
export PATRIOT_AUTO_COMMIT_CACHE=false
python -m patriot_center_backend.utils.update_all_caches
```

**Option 3: Remove from systemd service**
```bash
sudo nano /etc/systemd/system/patriot-center.service
# Remove or comment out: Environment="PATRIOT_AUTO_COMMIT_CACHE=true"
sudo systemctl daemon-reload
sudo systemctl restart patriot-center
```

## Security Considerations

1. **SSH Keys**: Private keys should never be committed to the repository
2. **PATs**: Store in secure locations with restricted permissions (600)
3. **Bot Identity**: Using a bot identity prevents personal credentials in automation
4. **Branch Strategy**: Creating feature branches before merging prevents direct pushes to main
5. **Git History**: All automated commits are clearly marked with bot identity

## Manual Override

If you need to manually update caches without auto-commit:

```bash
cd /opt/patriot-center
source venv/bin/activate
python -c "from patriot_center_backend.utils.update_all_caches import update_all_caches; update_all_caches(auto_commit=False)"
```
