from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from backend.repo_handler import clone_repo, cleanup_repo
from backend.log_parser import extract_errors
from backend.code_matcher import get_code_context
from backend.llm_agent import diagnose

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

    if not errors:
        return {"results": [], "message": "No errors found in log."}

    repo_path = clone_repo(repo_url)

    results = []
    try:
        for error in errors:
            code_snippet = get_code_context(repo_path, error["file"], error["line_number"])
            diagnosis = diagnose(error, code_snippet)

            results.append({
                "error_type": error["error_type"],
                "message": error["message"],
                "file": error["file"],
                "line_number": error["line_number"],
                "function": error.get("function"),
                "code_snippet": code_snippet,
                "root_cause": diagnosis.get("root_cause"),
                "suggested_fix": diagnosis.get("suggested_fix"),
                "confidence": diagnosis.get("confidence"),
            })
    finally:
        cleanup_repo(repo_path)

    return {"results": results}


@app.get("/")
def health_check():
    return {"status": "RepoDoctor API is running"}