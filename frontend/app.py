import streamlit as st
import requests

st.set_page_config(page_title="RepoDoctor", page_icon="🩺", layout="wide")

st.title("🩺 RepoDoctor")
st.caption("Paste a GitHub repo and a log file — get AI-diagnosed root causes and fixes.")

with st.form("diagnose_form"):
    repo_url = st.text_input("GitHub repo URL", placeholder="https://github.com/username/repo.git")
    log_file = st.file_uploader("Upload a log file", type=["log", "txt"])
    submitted = st.form_submit_button("Diagnose")

if submitted:
    if not repo_url or not log_file:
        st.error("Please provide both a repo URL and a log file.")
    else:
        with st.spinner("Cloning repo, parsing logs, and diagnosing errors..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/diagnose",
                    data={"repo_url": repo_url},
                    files={"log_file": (log_file.name, log_file.getvalue())},
                    timeout=120
                )
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                data = None

        if data:
            results = data.get("results", [])
            if not results:
                st.info(data.get("message", "No errors found."))
            else:
                st.success(f"Found {len(results)} error(s).")
                for i, r in enumerate(results, 1):
                    confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(r.get("confidence", "low"), "⚪")

                    with st.expander(f"{confidence_color} {r['error_type']} — {r['file']}:{r['line_number']}"):
                        code_snippet = r.get("code_snippet", "")
                        file_not_found = "[Could not find file" in code_snippet

                        if file_not_found:
                            st.warning(
                                "⚠️ Could not locate the source file in the repo. "
                                "This diagnosis is based on the error message alone and may be inaccurate. "
                                "Treat it as a starting hypothesis, not a confirmed root cause."
                            )
                        elif r.get("confidence") == "low":
                            st.info(
                                "ℹ️ The AI marked this diagnosis as low-confidence — "
                                "worth double-checking manually before applying the fix."
                            )

                        st.markdown(f"**Message:** {r['message']}")
                        st.markdown(f"**Function:** `{r.get('function', 'unknown')}`")

                        st.markdown("**Root Cause:**")
                        st.write(r.get("root_cause", "N/A"))

                        st.markdown("**Suggested Fix:**")
                        st.write(r.get("suggested_fix", "N/A"))

                        st.markdown("**Code Context:**")
                        st.code(code_snippet, language="python")