import pytest
import os
from actions.subagent import _write_file, _read_file, _edit_file, _run_command

def test_subagent_file_tools(tmp_path):
    f_path = tmp_path / "test.txt"
    _write_file(str(f_path), "hello world")
    assert _read_file(str(f_path)) == "hello world"
    
    _edit_file(str(f_path), "world", "gemini")
    assert _read_file(str(f_path)) == "hello gemini"

def test_subagent_run_command():
    out = _run_command("echo hello", ".")
    assert "hello" in out.lower()
