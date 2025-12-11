"""
Automated git commit utility for cache updates.

This module handles automatic commits and pushes of cache file updates to GitHub.
When cache files are updated on the production server, this utility:
1. Detects changes in the data/ directory
2. Creates a new branch with timestamp
3. Commits the changes
4. Pushes to GitHub and merges to main

The commits are made with a bot identity to distinguish automated updates
from manual developer commits.
"""
import os
import subprocess
from datetime import datetime
from pathlib import Path


# Git configuration for automated commits
GIT_AUTHOR_NAME = "Patriot Center Bot"
GIT_AUTHOR_EMAIL = "bot@patriotcenter.local"


def get_repo_root():
    """
    Find the git repository root directory.

    Returns:
        Path: Absolute path to the repository root

    Raises:
        RuntimeError: If not in a git repository
    """
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True,
            text=True,
            check=True
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise RuntimeError("Not in a git repository")


def has_cache_changes():
    """
    Check if there are uncommitted changes in the data/ directory.

    Returns:
        bool: True if there are changes in cache files, False otherwise
    """
    try:
        # Check for changes in the data directory
        result = subprocess.run(
            ['git', 'status', '--porcelain', 'patriot_center_backend/data/'],
            capture_output=True,
            text=True,
            check=True,
            cwd=get_repo_root()
        )
        # If output is not empty, there are changes
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error checking git status: {e}")
        return False


def commit_and_push_cache_updates():
    """
    Automatically commit and push cache file updates to GitHub.

    This function:
    1. Checks if there are changes in the data/ directory
    2. Creates a new branch named "cache-update-MM-DD-YY"
    3. Commits all changes with a descriptive message
    4. Pushes the branch to GitHub
    5. Merges the branch into main

    Returns:
        bool: True if commit/push succeeded, False otherwise
    """
    try:
        repo_root = get_repo_root()

        # Check if there are any changes to commit
        if not has_cache_changes():
            print("No cache changes detected. Skipping auto-commit.")
            return False

        # Generate branch name with current date
        today = datetime.now().strftime("%m-%d-%y")
        branch_name = f"cache-update-{today}"

        # Configure git author for this commit
        env = os.environ.copy()
        env['GIT_AUTHOR_NAME'] = GIT_AUTHOR_NAME
        env['GIT_AUTHOR_EMAIL'] = GIT_AUTHOR_EMAIL
        env['GIT_COMMITTER_NAME'] = GIT_AUTHOR_NAME
        env['GIT_COMMITTER_EMAIL'] = GIT_AUTHOR_EMAIL

        print(f"Creating branch: {branch_name}")

        # Fetch latest changes from origin
        subprocess.run(
            ['git', 'fetch', 'origin', 'main'],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Create and checkout new branch from origin/main
        subprocess.run(
            ['git', 'checkout', '-B', branch_name, 'origin/main'],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Stage all changes in the data directory
        subprocess.run(
            ['git', 'add', 'patriot_center_backend/data/'],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Create commit message with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Update cache data ({timestamp})\n\nAutomated cache update from production server."

        print(f"Committing changes: {commit_message}")

        # Commit the changes
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Push the branch to GitHub
        print(f"Pushing branch {branch_name} to GitHub...")
        subprocess.run(
            ['git', 'push', 'origin', branch_name],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Merge the branch into main (fast-forward)
        print("Merging into main...")
        subprocess.run(
            ['git', 'checkout', 'main'],
            cwd=repo_root,
            check=True,
            env=env
        )

        subprocess.run(
            ['git', 'merge', branch_name, '--ff-only'],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Push main to GitHub
        print("Pushing main to GitHub...")
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Clean up: delete the local branch
        print(f"Cleaning up local branch {branch_name}...")
        subprocess.run(
            ['git', 'branch', '-d', branch_name],
            cwd=repo_root,
            check=True,
            env=env
        )

        # Clean up: delete the remote branch from GitHub
        print(f"Deleting remote branch {branch_name} from GitHub...")
        subprocess.run(
            ['git', 'push', 'origin', '--delete', branch_name],
            cwd=repo_root,
            check=True,
            env=env
        )

        print(f"✅ Successfully committed and pushed cache updates to main")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during git operations: {e}")
        print(f"Command: {e.cmd}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"Unexpected error during auto-commit: {e}")
        return False


def setup_git_credentials():
    """
    Verify git credentials are configured for pushing to GitHub.

    This function checks if git can authenticate to GitHub. On the production
    server, you should have either:
    - SSH keys configured (~/.ssh/id_rsa with GitHub)
    - HTTPS with Personal Access Token configured

    Returns:
        bool: True if credentials appear to be configured
    """
    try:
        # Test if we can access the remote
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True,
            text=True,
            check=True,
            cwd=get_repo_root()
        )

        # Check if origin is configured
        if 'origin' in result.stdout:
            print("Git remote 'origin' is configured")
            return True
        else:
            print("Git remote 'origin' is not configured")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error checking git credentials: {e}")
        return False


if __name__ == "__main__":
    # Test the functionality
    print("Testing git auto-commit utility...")
    print(f"Repository root: {get_repo_root()}")
    print(f"Git credentials configured: {setup_git_credentials()}")
    print(f"Has cache changes: {has_cache_changes()}")

    # Uncomment to test commit/push (WARNING: will actually push to GitHub!)
    # commit_and_push_cache_updates()
