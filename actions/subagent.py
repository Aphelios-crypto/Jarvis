import os
import subprocess
from pathlib import Path

def _read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"

def _write_file(path: str, content: str) -> str:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def _edit_file(path: str, target: str, replacement: str) -> str:
    try:
        content = Path(path).read_text(encoding="utf-8")
        if target not in content:
            return f"Error: Target string not found in {path}"
        new_content = content.replace(target, replacement)
        Path(path).write_text(new_content, encoding="utf-8")
        return f"Successfully edited {path}"
    except Exception as e:
        return f"Error editing file: {e}"

def _run_command(command: str, cwd: str) -> str:
    try:
        result = subprocess.run(command, cwd=cwd, shell=True, capture_output=True, text=True, timeout=30)
        out = result.stdout + "\n" + result.stderr
        return out.strip() or "Command completed with no output."
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"

def _list_dir(path: str) -> str:
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"
