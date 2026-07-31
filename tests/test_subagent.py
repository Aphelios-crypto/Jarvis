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

def test_invoke_subagent(monkeypatch):
    from actions.subagent import invoke_subagent
    
    # Mock LLM behavior
    call_count = 0
    class MockModel:
        def generate_content(self, contents, config=None):
            nonlocal call_count
            call_count += 1
            class MockResponse:
                class Part:
                    class FuncCall:
                        name = "_run_command"
                        args = {"command": "echo test", "cwd": "."}
                    function_call = FuncCall() if call_count == 1 else None
                    text = "Final report." if call_count > 1 else None
                parts = [Part()]
                text = "Final report." if call_count > 1 else None
                function_calls = [Part.function_call] if call_count == 1 else None
                class Candidate:
                    class Content:
                        parts = parts
                    content = Content()
                candidates = [Candidate()]
            return MockResponse()

    class MockClient:
        class Models:
            def generate_content(self, model, contents, config=None):
                return MockModel().generate_content(contents, config=config)
        models = Models()

    monkeypatch.setattr("google.genai.Client", lambda api_key: MockClient())
    
    # Mock api key fetching
    import actions.computer_control
    monkeypatch.setattr(actions.computer_control, "_get_api_key", lambda: "test_key")
    
    res = invoke_subagent("Test instruction")
    assert "Final report" in res
    assert call_count == 2
