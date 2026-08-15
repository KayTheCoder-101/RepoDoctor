import os


def get_code_context(repo_path: str, file: str, line: int, window: int = 10) -> str:
    """
    Given a repo path, a relative file path, and a line number,
    return the code around that line as a string, with line numbers.
    """
    full_path = os.path.join(repo_path, file)

    if not os.path.exists(full_path):
        return f"[Could not find file: {file}]"

    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    total_lines = len(lines)
    start = max(0, line - window - 1)   # -1 because lines are 0-indexed here
    end = min(total_lines, line + window)

    snippet_lines = []
    for i in range(start, end):
        line_num = i + 1
        marker = ">>" if line_num == line else "  "
        snippet_lines.append(f"{marker} {line_num}: {lines[i].rstrip()}")

    return "\n".join(snippet_lines)


if __name__ == "__main__":
    # quick manual test — point this at a real file you have locally
    # e.g. test against this very file
    result = get_code_context(".", "backend/code_matcher.py", 10, window=5)
    print(result)