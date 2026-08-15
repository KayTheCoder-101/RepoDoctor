import streamlit as st
from collections import Counter
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.repo_handler import clone_repo, cleanup_repo, get_file_history
from backend.log_parser import extract_errors, extract_generic_errors
from backend.code_matcher import get_code_context
from backend.llm_agent import diagnose, correlate_errors

st.set_page_config(page_title="RepoDoctor", page_icon="🩺", layout="wide")

# ---------------------------------------------------------------------------
# GLOBAL STYLES
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }

    .stApp {
        background-color: #0B0D12;
    }

    #MainMenu, footer, header {display: none !important;}
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 880px;
        margin-left: auto !important;
        margin-right: auto !important;
    }
    [data-testid="stAppViewContainer"] {
        display: flex;
        justify-content: center;
    }

    /* ---------- Header ---------- */
    .rd-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 2px;
    }
    .rd-logo {
        font-size: 22px;
        font-weight: 700;
        color: #F5F7FA;
        letter-spacing: -0.02em;
    }
    .rd-tagline {
        color: #9AA3B2;
        font-size: 13px;
        margin-top: -6px;
        margin-bottom: 32px;
    }

    /* ---------- Hero ---------- */
    .rd-hero-title {
        font-size: 34px;
        font-weight: 800;
        color: #F5F7FA;
        letter-spacing: -0.03em;
        margin-bottom: 6px;
    }
    .rd-hero-sub {
        color: #9AA3B2;
        font-size: 15px;
        margin-bottom: 28px;
        line-height: 1.5;
    }

    /* ---------- Cards ---------- */
    .rd-card {
        background-color: #11141B;
        border: 1px solid #252A35;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
    }
    .rd-card-title {
        font-size: 15px;
        font-weight: 600;
        color: #F5F7FA;
        margin-bottom: 16px;
    }

    /* Streamlit input overrides */
    .stTextInput input {
        background-color: #161A23 !important;
        border: 1px solid #252A35 !important;
        color: #F5F7FA !important;
        border-radius: 8px !important;
        font-size: 14px !important;
    }
    .stTextInput input:focus {
        border-color: #4C7EF3 !important;
        box-shadow: 0 0 0 2px rgba(76,126,243,0.15) !important;
    }
    .stTextInput label, .stFileUploader label {
        color: #9AA3B2 !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background-color: #161A23 !important;
        border: 1.5px dashed #303645 !important;
        border-radius: 10px !important;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #4C7EF3 !important;
    }

    /* Primary button */
    .stButton button, .stFormSubmitButton button {
        background: linear-gradient(180deg, #4C7EF3, #3D6BDB) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 22px !important;
        transition: all 0.15s ease !important;
    }
    .stButton button:hover, .stFormSubmitButton button:hover {
        background: linear-gradient(180deg, #5B8AFF, #4C7EF3) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 14px rgba(76,126,243,0.3) !important;
    }

    /* ---------- Empty state ---------- */
    .rd-empty {
        text-align: center;
        padding: 40px 20px;
        color: #6B7280;
        font-size: 14px;
    }
    .rd-empty-title {
        color: #9AA3B2;
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 6px;
    }

    /* ---------- Status line ---------- */
    .rd-status {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 22px;
    }
    .rd-status-dot {
        width: 8px; height: 8px;
        background-color: #34D399;
        border-radius: 50%;
        display: inline-block;
    }
    .rd-status-title {
        font-size: 19px;
        font-weight: 700;
        color: #F5F7FA;
    }
    .rd-status-sub {
        color: #9AA3B2;
        font-size: 13px;
    }

    /* ---------- Metric cards ---------- */
    .rd-metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }
    .rd-metric {
        background-color: #11141B;
        border: 1px solid #252A35;
        border-radius: 12px;
        padding: 16px 18px;
    }
    .rd-metric-label {
        color: #9AA3B2;
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 6px;
    }
    .rd-metric-value {
        color: #F5F7FA;
        font-size: 26px;
        font-weight: 700;
    }

    /* ---------- Most affected file ---------- */
    .rd-file-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .rd-file-path {
        font-family: 'JetBrains Mono', monospace;
        color: #F5F7FA;
        font-size: 14px;
    }
    .rd-file-count {
        color: #9AA3B2;
        font-size: 12px;
        background-color: #161A23;
        border: 1px solid #252A35;
        border-radius: 20px;
        padding: 3px 10px;
    }

    /* ---------- Distribution rows ---------- */
    .rd-dist-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
        font-size: 13px;
    }
    .rd-dist-label {
        width: 140px;
        font-family: 'JetBrains Mono', monospace;
        color: #F5F7FA;
        flex-shrink: 0;
    }
    .rd-dist-bar-bg {
        flex: 1;
        background-color: #161A23;
        border-radius: 4px;
        height: 8px;
        overflow: hidden;
    }
    .rd-dist-bar {
        height: 100%;
        border-radius: 4px;
    }
    .rd-dist-count {
        width: 24px;
        text-align: right;
        color: #9AA3B2;
    }

    /* ---------- Severity badges ---------- */
    .rd-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .rd-badge-critical { background-color: rgba(248,81,73,0.15); color: #F87171; }
    .rd-badge-high { background-color: rgba(251,146,60,0.15); color: #FB923C; }
    .rd-badge-medium { background-color: rgba(250,204,21,0.15); color: #FACC15; }
    .rd-badge-low { background-color: rgba(96,165,250,0.15); color: #60A5FA; }

    .rd-error-title-row {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .rd-error-type {
        font-weight: 700;
        color: #F5F7FA;
        font-size: 14px;
    }
    .rd-error-loc {
        font-family: 'JetBrains Mono', monospace;
        color: #6B7280;
        font-size: 12px;
    }
    .rd-error-msg {
        font-family: 'JetBrains Mono', monospace;
        color: #F87171;
        font-size: 12px;
        background-color: rgba(248,81,73,0.08);
        padding: 2px 6px;
        border-radius: 4px;
    }

    .rd-section-label {
        color: #9AA3B2;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 16px;
        margin-bottom: 6px;
    }
    .rd-ai-tag {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        color: #A78BFA;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 16px;
        margin-bottom: 6px;
    }

    .rd-diff-before, .rd-diff-after {
        font-family: 'JetBrains Mono', monospace;
        font-size: 12.5px;
        padding: 8px 10px;
        border-radius: 6px;
        white-space: pre-wrap;
    }
    .rd-diff-before { background-color: rgba(248,81,73,0.08); color: #F87171; }
    .rd-diff-after { background-color: rgba(52,211,153,0.08); color: #34D399; }

    div[data-testid="stExpander"] {
        background-color: #11141B;
        border: 1px solid #252A35 !important;
        border-radius: 12px !important;
        margin-bottom: 10px;
    }
    div[data-testid="stExpander"] summary {
        padding: 14px 18px !important;
    }

    /* Hide empty Streamlit layout wrapper boxes */
    div[data-testid="stVerticalBlockBorderWrapper"]:empty,
    div[data-testid="element-container"]:empty,
    div[data-testid="stMarkdownContainer"]:empty,
    div[data-testid="stForm"]:empty,
    div[data-testid="stElementContainer"]:empty {
        display: none !important;
    }
    div[data-testid="stVerticalBlock"] > div:empty,
    div[data-testid="stHorizontalBlock"] > div:empty {
        display: none !important;
    }
    div[data-testid="stElementContainer"]:has(> div:empty:only-child) {
        display: none !important;
    }

    /* Style native Streamlit bordered containers as our cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #11141B !important;
        border: 1px solid #252A35 !important;
        border-radius: 14px !important;
        padding: 8px 16px !important;
        margin-bottom: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
SEVERITY_COLOR = {"critical": "#F87171", "high": "#FB923C", "medium": "#FACC15", "low": "#60A5FA"}
SEVERITY_CLASS = {"critical": "rd-badge-critical", "high": "rd-badge-high", "medium": "rd-badge-medium", "low": "rd-badge-low"}


def severity_badge(sev: str) -> str:
    sev = (sev or "medium").lower()
    if sev not in SEVERITY_CLASS:
        sev = "medium"
    return f'<span class="rd-badge {SEVERITY_CLASS[sev]}">● {sev}</span>'


# ---------------------------------------------------------------------------
# HEADER + HERO
# ---------------------------------------------------------------------------
st.markdown('<div class="rd-header"><span class="rd-logo">🩺 RepoDoctor</span></div>', unsafe_allow_html=True)
st.markdown('<div class="rd-tagline">AI-powered repository debugging</div>', unsafe_allow_html=True)

st.markdown('<div class="rd-hero-title">Diagnose your repository</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="rd-hero-sub">Connect your GitHub repository and upload the logs. '
    'RepoDoctor will identify the root cause and recommend a fix.</div>',
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------------
# INPUT WORKSPACE
# ---------------------------------------------------------------------------
with st.container(border=True):
    st.markdown('<div class="rd-card-title">Start a diagnosis</div>', unsafe_allow_html=True)
    with st.form("diagnose_form"):
        repo_url = st.text_input("Repository URL", placeholder="https://github.com/username/repository")
        log_file = st.file_uploader("Error / Log File", type=["log", "txt"])
        submitted = st.form_submit_button("✦ Diagnose Repository")

data = None
error_occurred = False
error_detail = ""

if submitted:
    if not repo_url or not log_file:
        st.error("Please provide both a repository URL and a log file.")
    else:
        with st.status("Analyzing repository...", expanded=True) as status:
            st.write("Fetching repository")
            st.write("Parsing logs")
            st.write("Detecting error patterns")
            st.write("Investigating root causes")
            st.write("Generating fixes")
            try:
                log_text = log_file.getvalue().decode("utf-8", errors="ignore")

                errors = extract_errors(log_text)
                generic_errors = extract_generic_errors(log_text)
                errors = errors + generic_errors

                if not errors:
                    data = {"results": [], "message": "No errors found in log."}
                else:
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
                                "fixed_line": diagnosis.get("fixed_line", ""),
                            })
                    finally:
                        cleanup_repo(repo_path)

                    correlation = correlate_errors(results)
                    data = {"results": results, "correlation": correlation}

                status.update(label="Diagnosis complete", state="complete", expanded=False)
            except Exception as e:
                error_occurred = True
                error_detail = str(e)
                status.update(label="Unable to complete diagnosis", state="error", expanded=False)

if error_occurred:
    st.error("**Unable to diagnose** — We couldn't analyze this repository. Please check the URL and log file, then try again.")
    with st.expander("View technical details"):
        st.code(error_detail)

# ---------------------------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------------------------
if not submitted and data is None:
    st.markdown(
        '<div class="rd-empty">'
        '<div class="rd-empty-title">Your repository health report will appear here</div>'
        'Once you run a diagnosis, RepoDoctor will summarize your errors, affected files, root causes, and recommended fixes.'
        '</div>',
        unsafe_allow_html=True
    )

# ---------------------------------------------------------------------------
# RESULTS
# ---------------------------------------------------------------------------
if data:
    results = data.get("results", [])

    if not results:
        st.info(data.get("message", "No errors found."))
    else:
        n = len(results)
        unique_types = len(set(r["error_type"] for r in results))
        unique_files = len(set(r["file"] for r in results if r["file"] and r["file"] != "unknown"))
        crit_high = sum(1 for r in results if (r.get("severity") or "").lower() in ("critical", "high"))

        st.markdown(
            f'<div class="rd-status">'
            f'<span class="rd-status-dot"></span>'
            f'<span class="rd-status-title">Diagnosis complete</span>'
            f'<span class="rd-status-sub">&nbsp;·&nbsp; {n} issue(s) found across {unique_files} file(s)</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="rd-metric-grid">'
            f'<div class="rd-metric"><div class="rd-metric-label">Errors</div><div class="rd-metric-value">{n}</div></div>'
            f'<div class="rd-metric"><div class="rd-metric-label">Error Types</div><div class="rd-metric-value">{unique_types}</div></div>'
            f'<div class="rd-metric"><div class="rd-metric-label">Files Affected</div><div class="rd-metric-value">{unique_files}</div></div>'
            f'<div class="rd-metric"><div class="rd-metric-label">Critical / High</div><div class="rd-metric-value">{crit_high}</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Most affected file
        file_counts = Counter(r["file"] for r in results)
        if file_counts:
            top_file, top_count = file_counts.most_common(1)[0]
            with st.container(border=True):
                st.markdown('<div class="rd-card-title">Most affected file</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="rd-file-card">'
                    f'<span class="rd-file-path">📄 {top_file}</span>'
                    f'<span class="rd-file-count">{top_count} error(s)</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Error distribution
        type_counts = Counter(r["error_type"] for r in results)
        max_count = max(type_counts.values()) if type_counts else 1
        with st.container(border=True):
            st.markdown('<div class="rd-card-title">Error distribution</div>', unsafe_allow_html=True)
            for error_type, count in type_counts.most_common():
                pct = int((count / max_count) * 100)
                st.markdown(
                    f'<div class="rd-dist-row">'
                    f'<span class="rd-dist-label">{error_type}</span>'
                    f'<span class="rd-dist-bar-bg"><span class="rd-dist-bar" style="width:{pct}%; background-color:#4C7EF3;"></span></span>'
                    f'<span class="rd-dist-count">{count}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

        # Correlation
        correlation = data.get("correlation", {}) or {}
        groups = correlation.get("groups", [])
        summary = correlation.get("summary", "")
        if summary or groups:
            with st.container(border=True):
                st.markdown('<div class="rd-card-title">🔗 Related errors</div>', unsafe_allow_html=True)
                if summary:
                    st.write(summary)
                for group in groups:
                    indices = group.get("error_indices", [])
                    shared_cause = group.get("shared_cause", "")
                    labels = [
                        f"{results[i]['error_type']} ({results[i]['file']}:{results[i]['line_number']})"
                        for i in indices if i < len(results)
                    ]
                    st.info(f"**{' + '.join(labels)}**\n\n{shared_cause}")

        # ---------------- Detected issues ----------------
        st.markdown('<div class="rd-card-title" style="margin-top:8px;">Detected issues</div>', unsafe_allow_html=True)

        # Filter toolbar (only if useful)
        filtered_results = results
        if n > 1:
            available_severities = sorted(
                set((r.get("severity") or "medium").lower() for r in results),
                key=lambda s: SEVERITY_ORDER.get(s, 4)
            )
            filter_options = ["All"] + [s.capitalize() for s in available_severities]
            selected = st.radio("Filter by severity", filter_options, horizontal=True, label_visibility="collapsed")
            if selected != "All":
                filtered_results = [r for r in results if (r.get("severity") or "medium").lower() == selected.lower()]

        if n > 5:
            search_term = st.text_input("⌕ Search errors...", placeholder="Search by type, file, or message", label_visibility="collapsed")
            if search_term:
                st_lower = search_term.lower()
                filtered_results = [
                    r for r in filtered_results
                    if st_lower in r["error_type"].lower()
                    or st_lower in str(r["file"]).lower()
                    or st_lower in r["message"].lower()
                ]

        filtered_results = sorted(filtered_results, key=lambda r: SEVERITY_ORDER.get((r.get("severity") or "medium").lower(), 4))

        for r in filtered_results:
            sev = (r.get("severity") or "medium").lower()
            conf = (r.get("confidence") or "medium").lower()

            title_html = (
                f'{severity_badge(sev)} '
                f'<span class="rd-error-type">{r["error_type"]}</span> '
                f'<span class="rd-error-loc">{r["file"]}:{r["line_number"]}</span>'
            )

            with st.expander(f"{sev.upper()} · {r['error_type']} · {r['file']}:{r['line_number']}"):
                st.markdown(title_html, unsafe_allow_html=True)
                st.markdown(f'<div class="rd-error-msg">{r["message"]}</div>', unsafe_allow_html=True)

                code_snippet = r.get("code_snippet", "")
                file_not_found = "[Could not find file" in code_snippet or "[No source location" in code_snippet

                if file_not_found:
                    st.warning(
                        "⚠️ Could not locate the source file in the repo. "
                        "This diagnosis is based on the error message alone and may be inaccurate."
                    )
                elif conf == "low":
                    st.info("ℹ️ Low-confidence diagnosis — worth double-checking manually.")

                st.markdown('<div class="rd-ai-tag">✦ AI diagnosis</div>', unsafe_allow_html=True)
                st.write(r.get("root_cause", "N/A"))

                st.markdown('<div class="rd-section-label">Recommended fix</div>', unsafe_allow_html=True)
                st.write(r.get("suggested_fix", "N/A"))

                st.markdown('<div class="rd-section-label">Code context</div>', unsafe_allow_html=True)
                st.code(code_snippet, language="python")

                fixed_line = r.get("fixed_line", "")
                if fixed_line:
                    original_line = ""
                    for line in code_snippet.split("\n"):
                        if line.strip().startswith(">>"):
                            original_line = line.split(":", 1)[-1].strip() if ":" in line else line.replace(">>", "").strip()
                            break

                    st.markdown('<div class="rd-section-label">Suggested change</div>', unsafe_allow_html=True)
                    if original_line:
                        st.markdown(f'<div class="rd-diff-before">- {original_line}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="rd-diff-after">+ {fixed_line}</div>', unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown('<div class="rd-section-label">Confidence</div>', unsafe_allow_html=True)
                    st.write(conf.capitalize())
                with col_b:
                    st.markdown('<div class="rd-section-label">Severity</div>', unsafe_allow_html=True)
                    st.write(sev.capitalize())
