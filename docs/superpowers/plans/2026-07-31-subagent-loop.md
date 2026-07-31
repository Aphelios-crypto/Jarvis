# Subagent Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a generic `invoke_subagent` tool to Jarvis that spins up a Gemini 3.1 Pro High instance in a loop, equipped with code editing and terminal tools, to execute complex autonomous tasks.

**Architecture:** A new `actions/subagent.py` file will contain the loop. The loop uses Google GenAI SDK's `generate_content` and executes `function_calls` sequentially until the model returns a final text response.

**Tech Stack:** Python, Google GenAI SDK (Gemini 3.1 Pro High), Subprocess.

## Global Constraints

- Limit the loop to 30 iterations max.
- Shell commands (`run_command`) must have a timeout of 30 seconds.
- The `invoke_subagent` must be explicitly listed in `TOOL_DECLARATIONS` in `main.py`.
- No placeholders or stubbing in implementation steps.

---

### Task 1: Create the Tools and the Subagent File

**Files:**
- Create: `actions/subagent.py`
- Test: `tests/test_subagent.py` (Create if missing)

**Interfaces:**
- Produces: Python helper functions `_read_file`, `_write_file`, `_edit_file`, `_run_command`, `_list_dir`.

- [ ] **Step 1: Write the failing test for the tools**

```python
# tests/test_subagent.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_subagent.py -v`
Expected: FAIL (ModuleNotFoundError for `actions.subagent`)

- [ ] **Step 3: Implement the basic tools**

```python
# actions/subagent.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_subagent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_subagent.py actions/subagent.py
git commit -m "feat: add file and terminal tools for subagent"
```

---

### Task 2: Implement the Agent Loop

**Files:**
- Modify: `actions/subagent.py`

**Interfaces:**
- Consumes: `actions.computer_control._get_api_key`
- Produces: `invoke_subagent(instruction: str, ui_logger=None) -> str`

- [ ] **Step 1: Write the failing test for the loop**

```python
# tests/test_subagent.py
# Add to the end of the file:
def test_invoke_subagent(monkeypatch):
    from actions.subagent import invoke_subagent
    
    # Mock LLM behavior
    call_count = 0
    class MockModel:
        def generate_content(self, contents, tools):
            nonlocal call_count
            call_count += 1
            class MockResponse:
                class Part:
                    class FuncCall:
                        name = "run_command"
                        args = {"command": "echo test", "cwd": "."}
                    function_call = FuncCall() if call_count == 1 else None
                    text = "Final report." if call_count > 1 else None
                parts = [Part()]
                text = "Final report." if call_count > 1 else None
            return MockResponse()

    class MockClient:
        class Models:
            def generate_content(self, model, contents, tools):
                return MockModel().generate_content(contents, tools)
        models = Models()

    monkeypatch.setattr("google.genai.Client", lambda api_key: MockClient())
    
    res = invoke_subagent("Test instruction")
    assert "Final report" in res
    assert call_count == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_subagent.py::test_invoke_subagent -v`
Expected: FAIL (ImportError for invoke_subagent)

- [ ] **Step 3: Write the loop implementation**

```python
# actions/subagent.py
# Add to the bottom of the file:
from google import genai
from google.genai import types

def invoke_subagent(instruction: str, ui_logger=None) -> str:
    from actions.computer_control import _get_api_key
    client = genai.Client(api_key=_get_api_key())
    
    tools = [_read_file, _write_file, _edit_file, _run_command, _list_dir]
    
    system_instruction = "You are an autonomous subagent. You have tools to write code, read files, and run commands. Complete the user's objective. Once you are fully done, provide a final summary without calling any more tools."
    
    contents = [types.Content(role="user", parts=[types.Part.from_text(instruction)])]
    
    max_turns = 30
    
    for turn in range(max_turns):
        response = client.models.generate_content(
            model='gemini-3.1-pro',
            contents=contents,
            config=types.GenerateContentConfig(
                tools=tools,
                system_instruction=system_instruction
            )
        )
        
        contents.append(response.candidates[0].content)
        
        if not response.function_calls:
            return response.text or "Completed without final text response."
            
        for fc in response.function_calls:
            name = fc.name
            args = {k: v for k, v in fc.args.items()}
            
            if ui_logger:
                ui_logger(f"Subagent calling: {name}")
                
            try:
                if name == "_read_file":
                    res = _read_file(**args)
                elif name == "_write_file":
                    res = _write_file(**args)
                elif name == "_edit_file":
                    res = _edit_file(**args)
                elif name == "_run_command":
                    res = _run_command(**args)
                elif name == "_list_dir":
                    res = _list_dir(**args)
                else:
                    res = f"Error: Unknown function {name}"
            except Exception as e:
                res = f"Tool execution failed: {str(e)}"
                
            func_resp_part = types.Part.from_function_response(
                name=name,
                response={"result": res}
            )
            contents.append(types.Content(role="user", parts=[func_resp_part]))
            
    return "Error: Subagent hit max turns (30) before completion."
```

- [ ] **Step 4: Run tests to verify**

Run: `pytest tests/test_subagent.py::test_invoke_subagent -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add actions/subagent.py tests/test_subagent.py
git commit -m "feat: implement subagent execution loop with genai SDK"
```

---

### Task 3: Expose to Jarvis Main Loop

**Files:**
- Modify: `main.py`
- Modify: `core/prompt.txt`

**Interfaces:**
- Consumes: `actions.subagent.invoke_subagent`

- [ ] **Step 1: Add to `prompt.txt`**

```text
# Modify core/prompt.txt - append to TOOL ROUTING:
- invoke_subagent: ONLY for complex programming, refactoring, or multi-step OS tasks. Tell the subagent exactly what you need built or investigated. It runs in the background and returns a final text report.
```

- [ ] **Step 2: Add to `TOOL_DECLARATIONS` in `main.py`**

Find `TOOL_DECLARATIONS` list in `main.py` and append:
```python
    {
        "name": "invoke_subagent",
        "description": "Spawns a powerful autonomous subagent to write code, debug issues, or execute multi-step OS terminal commands in the background.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "instruction": {"type": "STRING", "description": "The exact objective the subagent needs to accomplish."}
            },
            "required": ["instruction"]
        }
    },
```

- [ ] **Step 3: Import and wire it in `main.py`**

Find the imports in `main.py` (around line 60) and add:
```python
from actions.subagent import invoke_subagent
```

Then locate where tools are dispatched. Since we can't see the exact dispatch switch case easily, look for the text `"invoke_subagent"` handling. If the dispatch is dynamic (e.g., `globals()[name]`), the import is enough. For safety, ensure it handles `invoke_subagent` explicitly if there's a big if-else block. *(The implementer will search for `open_app` or `file_processor` in `main.py` to match the exact dispatch pattern).*

- [ ] **Step 4: Commit**

```bash
git add main.py core/prompt.txt
git commit -m "feat: expose invoke_subagent tool to main Jarvis brain"
```
