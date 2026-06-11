"""
Step 4: Code Sandbox — Safe Python execution for physics calculations.

Executes LLM-generated Python code in a restricted environment.
Extracts `answer` and `unit` variables from the executed code.
Includes retry mechanism with error feedback.
"""
import math
import re
import signal
import sys
import traceback
from typing import Any

from app.config import config
from app.models import SandboxResult


# Allowed modules and builtins for the sandbox
SAFE_BUILTINS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "int": int,
    "float": float,
    "str": str,
    "len": len,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "sum": sum,
    "pow": pow,
    "print": lambda *args, **kwargs: None,  # Suppress print
    "True": True,
    "False": False,
    "None": None,
}

SAFE_MODULES = {
    "math": math,
}


def _validate_code(code: str) -> str | None:
    """
    Pre-check code for safety and correctness.
    Returns error message if invalid, None if OK.
    """
    if not code or not code.strip():
        return "Empty code block"

    # Check for required output variables
    if not re.search(r"\banswer\s*=", code):
        return "Code must define an 'answer' variable"
    if not re.search(r"\bunit\s*=", code):
        return "Code must define a 'unit' variable"

    # Block dangerous operations
    dangerous = [
        "import os", "import sys", "import subprocess",
        "__import__", "eval(", "exec(", "open(",
        "os.system", "os.popen", "subprocess",
        "shutil", "glob", "pathlib",
    ]
    for d in dangerous:
        if d in code:
            return f"Blocked: '{d}' is not allowed in sandbox"

    return None


def _execute_code(code: str, timeout: int = 5) -> dict:
    """
    Execute Python code in a restricted sandbox.
    
    Returns dict with keys: success, answer, unit, error, output
    """
    # Pre-validation
    error = _validate_code(code)
    if error:
        return {"success": False, "error": error}

    # Prepare execution environment
    safe_globals = {"__builtins__": SAFE_BUILTINS}
    safe_globals.update(SAFE_MODULES)
    local_vars = {}

    # Allow 'import math' in code by pre-injecting
    code = code.replace("import math", "# math already imported")
    code = code.replace("from math import", "# math already available\n# from math import")

    try:
        # Compile first to catch syntax errors
        compiled = compile(code, "<sandbox>", "exec")

        # Execute with timeout (Windows-compatible: use simple exec)
        exec(compiled, safe_globals, local_vars)

        # Extract results
        answer = local_vars.get("answer")
        unit = local_vars.get("unit", "")

        if answer is None:
            return {"success": False, "error": "'answer' variable was not set"}

        # Format answer
        if isinstance(answer, float):
            # Avoid floating point noise: round to reasonable precision
            if abs(answer) > 0 and abs(answer) < 1e-10:
                answer_str = f"{answer:.4e}"
            elif abs(answer) > 1e6:
                answer_str = f"{answer:.4e}"
            else:
                # Remove trailing zeros
                answer_str = f"{answer:.6g}"
        else:
            answer_str = str(answer)

        return {
            "success": True,
            "answer": answer_str,
            "unit": str(unit) if unit else "",
        }

    except SyntaxError as e:
        return {"success": False, "error": f"SyntaxError: {e}"}
    except ZeroDivisionError:
        return {"success": False, "error": "ZeroDivisionError: division by zero"}
    except OverflowError:
        return {"success": False, "error": "OverflowError: result too large"}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {e}"}


def execute_sandbox(
    python_code: str,
    max_retries: int | None = None,
    question: str = "",
    premises: list[str] | None = None,
) -> SandboxResult:
    """
    Step 4: Execute Python code safely and extract answer + unit.
    
    Includes self-repair: if code fails, can retry with error feedback
    (retry with LLM is handled at pipeline level).
    
    Args:
        python_code: The Python code string to execute.
        max_retries: Max retry attempts (not used here; retries happen at pipeline level).
        question: Original question (for error context).
        premises: Original premises (for error context).
        
    Returns:
        SandboxResult with success status, answer, unit, error.
    """
    if max_retries is None:
        max_retries = config.sandbox_max_retries

    result = _execute_code(python_code, timeout=config.sandbox_timeout)

    return SandboxResult(
        success=result.get("success", False),
        answer_value=result.get("answer"),
        unit=result.get("unit"),
        error=result.get("error"),
        retries_used=0,
    )
