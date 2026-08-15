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


if __name__ == "__main__":
    # quick manual test — clone a small public repo
    test_url = "https://github.com/octocat/Hello-World.git"
    path = clone_repo(test_url)
    print(f"Cloned to: {path}")
    print("Contents:", os.listdir(path))

    cleanup_repo(path)
    print("Cleaned up.")