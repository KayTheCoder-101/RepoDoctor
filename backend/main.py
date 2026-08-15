from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from backend.repo_handler import clone_repo, cleanup_repo, get_file_history
from backend.log_parser import extract_errors, extract_generic_errors
from backend.code_matcher import get_code_context
from backend.llm_agent import diagnose, correlate_errors

app = FastAPI(title="RepoDoctor")

# Allow the Streamlit frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/diagnose")
async def diagnose_endpoint(
    repo_url: str = Form(...),
    log_file: UploadFile = File(...)
):
    """
    Takes a GitHub repo URL and a log file.
    Returns a list of diagnosed errors.
    """
    log_bytes = await log_file.read()
    log_text = log_bytes.decode("utf-8", errors="ignore")

    errors = extract_errors(log_text)
    generic_errors = extract_generic_errors(log_text)
    errors = errors + generic_errors

    if not errors:
        return {"results": [], "message": "No errors found in log."}

    repo_path = clone_repo(repo_url)

    results = []
    try:
        for error in errors:
            if error.get("file") and error.get("line_number"):
                code_snippet = get_code_context(repo_path, error["file"], error["line_number"])
                file_history = get_file_history(repo_path, error["file"], error["line_number"])
            else:
                code_snippet = "[No source location available for this error]"
                file_history = ""

            diagnosis = diagnose(error, code_snippet, file_history)

            results.append({
                "error_type": error["error_type"],
                "message": error["message"],
                "file": error.get("file") or "unknown",
                "line_number": error.get("line_number") or 0,
                "function": error.get("function"),
                "code_snippet": code_snippet,
                "root_cause": diagnosis.get("root_cause"),
                "suggested_fix": diagnosis.get("suggested_fix"),
                "confidence": diagnosis.get("confidence"),
                "severity": diagnosis.get("severity", "medium"),
            })
    finally:
        cleanup_repo(repo_path)

    correlation = correlate_errors(results)

    return {"results": results, "correlation": correlation}


@app.get("/")
def health_check():
    return {"status": "RepoDoctor API is running"}