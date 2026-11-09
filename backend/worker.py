import ast
import os
import re
import docker
from celery import Celery
from database import SessionLocal, Submission, SubmissionStatus

try:
    import autoflake
except ImportError:  # pragma: no cover - handled when auto-fix is requested
    autoflake = None

try:
    import autopep8
except ImportError:  # pragma: no cover - handled at runtime in the API
    autopep8 = None

celery_app = Celery("linter_worker", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

PENALTY_WEIGHTS = {
    "Convention": 2.0,
    "Refactor": 3.0,
    "Warning": 5.0,
    "Security": 10.0
}

def get_docker_client():
    return docker.from_env()

def _syntax_error_progressed(previous: SyntaxError, current: SyntaxError) -> bool:
    previous_position = (previous.lineno or 0, previous.offset or 0)
    current_position = (current.lineno or 0, current.offset or 0)
    if current_position > previous_position:
        return True
    if "was never closed" in previous.msg and "was never closed" in current.msg:
        return current_position != previous_position
    return current.msg != previous.msg

def _syntax_repair_candidates(code: str, error: SyntaxError) -> list[str]:
    if error.lineno is None:
        return []

    lines = code.splitlines(keepends=True)
    line_index = error.lineno - 1
    if line_index < 0 or line_index >= len(lines):
        return []

    line = lines[line_index]
    line_content = line.rstrip("\r\n")
    line_start = sum(len(item) for item in lines[:line_index])
    local_offset = max(0, (error.offset or 1) - 1)
    candidates = []

    if error.msg == "expected ':'":
        stripped_line = line_content.rstrip()
        if re.fullmatch(r"\s*(?:async\s+)?def\s+[A-Za-z_]\w*\s*\(.*\)", stripped_line):
            trailing_whitespace = line_content[len(stripped_line):]
            newline = line[len(line_content):]
            repaired_line = f"{stripped_line}:{trailing_whitespace}{newline}"
            return ["".join(lines[:line_index] + [repaired_line] + lines[line_index + 1:])]

    if "Perhaps you forgot a comma?" in error.msg:
        insertion = line_start + min(error.offset or 0, len(line_content))
        candidates.append(code[:insertion] + "," + code[insertion:])

    unclosed = re.fullmatch(r"'([\(\[\{])' was never closed", error.msg)
    if unclosed:
        closer = {"(": ")", "[": "]", "{": "}"}[unclosed.group(1)]
        insertion = len(code.rstrip("\r\n"))
        candidates.append(code[:insertion] + closer + code[insertion:])

    unmatched = re.fullmatch(r"unmatched '([\)\]\}])'", error.msg)
    if unmatched:
        opener = {")": "(", "]": "[", "}": "{"}[unmatched.group(1)]
        closer_position = min(local_offset, len(line_content))
        for token in re.finditer(r"[A-Za-z_]\w*|\d+(?:\.\d+)?|\"[^\"]*\"|'[^']*'", line_content[:closer_position]):
            insertion = line_start + token.start()
            candidates.append(code[:insertion] + opener + code[insertion:])

    if error.msg == "invalid syntax" and error.offset:
        split_at = min(local_offset, len(line_content))
        prefix = line_content[:split_at].rstrip()
        suffix = line_content[split_at:].lstrip()
        if prefix and suffix:
            indentation = line_content[:len(line_content) - len(line_content.lstrip())]
            newline = "\r\n" if line.endswith("\r\n") else "\n"
            replacement = f"{prefix}{newline}{indentation}{suffix}{line[len(line_content):]}"
            candidates.append("".join(lines[:line_index] + [replacement] + lines[line_index + 1:]))

    return list(dict.fromkeys(candidates))

def fix_python_code(code: str) -> str:
    if code is None:
        raise ValueError("Python code is required for auto-fix.")

    if not code.strip():
        return code

    if autoflake is None or autopep8 is None:
        raise RuntimeError(
            "Auto-fix dependencies are missing. From backend, run: "
            "./.venv315/Scripts/python.exe -m pip install -r requirements.txt"
        )

    for _ in range(10):
        try:
            ast.parse(code)
            break
        except SyntaxError as exc:
            valid_candidates = []
            progressed_candidates = []
            for candidate in _syntax_repair_candidates(code, exc):
                try:
                    parsed = ast.parse(candidate)
                    valid_candidates.append((candidate, ast.dump(parsed, include_attributes=False)))
                except SyntaxError as next_error:
                    if _syntax_error_progressed(exc, next_error):
                        progressed_candidates.append(candidate)

            valid_trees = {tree for _, tree in valid_candidates}
            if len(valid_trees) == 1:
                code = valid_candidates[0][0]
                continue
            if not valid_candidates and len(progressed_candidates) == 1:
                code = progressed_candidates[0]
                continue

            raise ValueError(
                f"Could not safely auto-fix syntax error at line {exc.lineno}, "
                f"column {exc.offset}: {exc.msg}"
            ) from exc
    else:
        raise ValueError("Could not safely auto-fix all syntax errors in this file.")

    code = autoflake.fix_code(
        code,
        remove_all_unused_imports=True,
        remove_unused_variables=True,
    )

    try:
        fixed_code = autopep8.fix_code(code, options={"aggressive": 1})
    except Exception as exc:  # pragma: no cover - depends on source validity
        raise ValueError(f"Could not auto-fix the Python source: {exc}") from exc

    return fixed_code if fixed_code is not None else code

@celery_app.task(name="tasks.run_static_analysis")
def run_static_analysis(submission_id: str, file_path: str, language: str):
    db = SessionLocal()
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        return

    submission.status = SubmissionStatus.PROCESSING
    db.commit()

    try:
        diagnostics = []
        filename = os.path.basename(file_path)
        host_dir = os.path.dirname(os.path.abspath(file_path))

        if language.lower() == "python":
            docker_client = get_docker_client()

            # Run Flake8 inside isolated ephemeral container
            container = docker_client.containers.run(
                image="alpine-python-linter:latest",
                command=["flake8", "--format=%(row)d|%(col)d|%(code)s|%(text)s", "--", filename],
                volumes={host_dir: {"bind": "/code", "mode": "ro"}},
                working_dir="/code",
                network_mode="none",
                mem_limit="512m",
                nano_cpus=1000000000, # 1 CPU
                read_only=True,
                user="10001:10001",
                detach=True,
                remove=False
            )

            try:
                exit_status = container.wait().get("StatusCode")
                raw_output = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
                error_output = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            finally:
                container.remove(force=True)

            if exit_status not in (0, 1):
                raise RuntimeError(
                    f"Flake8 exited with status {exit_status}: {error_output.strip() or raw_output.strip()}"
                )

            for output_line in raw_output.splitlines():
                if not output_line.strip():
                    continue

                parts = output_line.split("|", 3)
                if len(parts) != 4:
                    raise ValueError(f"Could not parse Flake8 output: {output_line}")

                line_number, column_number, rule_code, message = parts
                diagnostics.append({
                    "rule_code": rule_code,
                    "line": int(line_number),
                    "column": int(column_number),
                    "message": message,
                    "severity": "Convention" if rule_code.startswith("E") else "Refactor"
                })

        # Calculate Quality Score
        total_penalty = sum(PENALTY_WEIGHTS.get(item["severity"], 2.0) for item in diagnostics)
        quality_score = max(0.0, round(100.0 - total_penalty, 2))

        submission.quality_score = quality_score
        submission.report_json = diagnostics
        submission.status = SubmissionStatus.COMPLETED

    except Exception as e:
        submission.status = SubmissionStatus.FAILED
        submission.report_json = [{"rule_code": "EXEC_ERR", "line": 1, "column": 1, "message": str(e), "severity": "Security"}]
    
    finally:
        db.commit()
        db.close()