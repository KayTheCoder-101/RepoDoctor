import os
import tempfile
import shutil
import git


def clone_repo(github_url: str) -> str:
    """
    Clone a GitHub repo into a temporary directory.
    Returns the local path to the cloned repo.
    """
    temp_dir = tempfile.mkdtemp(prefix="repodoctor_")

    try:
        git.Repo.clone_from(github_url, temp_dir)
    except git.exc.GitCommandError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ValueError(f"Failed to clone repo: {e}")

    return temp_dir


def cleanup_repo(local_path: str):
    """Delete the cloned repo directory."""
    shutil.rmtree(local_path, ignore_errors=True)

def get_file_history(repo_path: str, file: str, line: int, max_commits: int = 3) -> str:
    """
    Get recent commit history for the specific file, focused on the area around `line`.
    Returns a summary string of recent changes, or empty string if none found.
    """
    try:
        repo = git.Repo(repo_path)
        commits = list(repo.iter_commits(paths=file, max_count=max_commits))

        if not commits:
            return ""

        history_parts = []
        for commit in commits:
            history_parts.append(
                f"- {commit.hexsha[:7]} ({commit.committed_datetime.strftime('%Y-%m-%d')}): {commit.summary}"
            )

        return "Recent commits touching this file:\n" + "\n".join(history_parts)

    except Exception as e:
        return ""

if __name__ == "__main__":
    # quick manual test — clone a small public repo
    test_url = "https://github.com/octocat/Hello-World.git"
    path = clone_repo(test_url)
    print(f"Cloned to: {path}")
    print("Contents:", os.listdir(path))

    cleanup_repo(path)
    print("Cleaned up.")