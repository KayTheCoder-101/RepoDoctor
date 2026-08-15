import re


def extract_errors(log_text: str) -> list[dict]:
    """
    Parse raw log text and return a list of structured errors.
    Each error dict: {error_type, message, file, line_number, raw_trace}
    """
    errors = []

    # Split log into traceback blocks
    # Python tracebacks start with "Traceback (most recent call last):"
    blocks = log_text.split("Traceback (most recent call last):")

    for block in blocks[1:]:  # skip text before the first traceback
        # Find all "File "path", line N, in function" entries
        file_lines = re.findall(r'File "(.+?)", line (\d+), in (\S+)', block)

        # Find the final error line, e.g. "ValueError: something went wrong"
        error_match = re.search(r'\n(\w+(?:Error|Exception)): (.+)', block)

        if file_lines and error_match:
            last_file, last_line, last_func = file_lines[-1]
            error_type = error_match.group(1)
            message = error_match.group(2).strip()

            errors.append({
                "error_type": error_type,
                "message": message,
                "file": last_file,
                "line_number": int(last_line),
                "function": last_func,
                "raw_trace": "Traceback (most recent call last):" + block.split(error_match.group(0))[0] + error_match.group(0)
            })

    return errors


def extract_generic_errors(log_text: str) -> list[dict]:
    """
    Parse generic single-line error logs, e.g.:
    2026-08-15 14:32:01 ERROR [module.name] Something went wrong: connection refused

    Returns errors in the same shape as extract_errors, but file/line_number
    will be None since generic logs don't include source location.
    """
    errors = []

    pattern = re.compile(
        r'^.*?\b(ERROR|CRITICAL|FATAL)\b\s*(?:\[[^\]]*\])?\s*[:\-]?\s*(.+)$',
        re.IGNORECASE | re.MULTILINE
    )

    for match in pattern.finditer(log_text):
        level = match.group(1).upper()
        message = match.group(2).strip()

        if not message:
            continue

        errors.append({
            "error_type": level,
            "message": message,
            "file": None,
            "line_number": None,
            "function": None,
            "raw_trace": match.group(0).strip()
        })

    return errors


if __name__ == "__main__":
    sample_log = '''
Traceback (most recent call last):
  File "app.py", line 55, in main
    process_data(items)
  File "app.py", line 42, in process_data
    result = 10 / count
ZeroDivisionError: division by zero
'''
    result = extract_errors(sample_log)
    import json
    print(json.dumps(result, indent=2))

    generic_log = "2026-08-15 14:32:01 ERROR [module.name] Something went wrong: connection refused"
    print(json.dumps(extract_generic_errors(generic_log), indent=2))
