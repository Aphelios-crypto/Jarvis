# Visual GUI Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a vision-action loop using Gemini 3.1 High and pyautogui to allow Jarvis to visually interact with any application on the screen.

**Architecture:** A new `gui_agent.py` module will take a screenshot, pass it to Gemini 3.1 High with a specific prompt, parse the returned JSON to find the next action and (X, Y) coordinates, and execute the action using `pyautogui` via the existing `computer_control.py` primitives. The loop repeats until the goal is achieved. 

**Tech Stack:** Python, Playwright, mss/pyautogui, Google GenAI SDK (Gemini 3.1 High).

## Global Constraints

- Must use Gemini 3.1 High for the vision loop.
- Must limit the vision loop to 10 iterations max to prevent infinite loops.
- Do not create a new pyautogui wrapper, use the existing `actions/computer_control.py` functions where possible.

---

### Task 1: Create `gui_agent.py` Loop Structure and Failsafes

**Files:**
- Create: `actions/gui_agent.py`
- Test: `tests/test_gui_agent.py`

**Interfaces:**
- Consumes: `actions.computer_control._click`, `actions.computer_control._smart_type`, `actions.screen_processor._compress`
- Produces: `def execute_gui_action(goal: str) -> str`

- [ ] **Step 1: Write the failing test for the loop limit**

```python
# tests/test_gui_agent.py
import pytest
from actions.gui_agent import execute_gui_action

def test_execute_gui_action_loop_limit(monkeypatch):
    # Mock the LLM call to always return an action that isn't 'done'
    def mock_llm_call(*args, **kwargs):
        return '{"action": "click", "x": 100, "y": 100, "reasoning": "mock"}'
    
    monkeypatch.setattr("actions.gui_agent._call_vision_llm", mock_llm_call)
    
    # Mock screenshot and click so we don't actually take control of the PC in tests
    monkeypatch.setattr("actions.gui_agent._take_screenshot", lambda: b"fake_bytes")
    monkeypatch.setattr("actions.computer_control._click", lambda x, y: "clicked")
    
    result = execute_gui_action("Do something impossible")
    assert "loop limit reached" in result.lower() or "aborted" in result.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gui_agent.py::test_execute_gui_action_loop_limit -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

- [ ] **Step 3: Write minimal implementation**

```python
# actions/gui_agent.py
import json
import time

# Stubbed for now, implemented in next task
def _call_vision_llm(goal: str, screenshot_bytes: bytes) -> str:
    return '{"action": "done", "reasoning": "Not implemented"}'

def _take_screenshot() -> bytes:
    return b""

def execute_gui_action(goal: str) -> str:
    max_steps = 10
    steps = 0
    
    while steps < max_steps:
        screenshot = _take_screenshot()
        response = _call_vision_llm(goal, screenshot)
        
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            return "Failed to parse LLM response"
            
        action = data.get("action")
        if action == "done":
            return f"Goal achieved: {goal}"
            
        from actions import computer_control
        if action == "click":
            computer_control._click(data.get("x"), data.get("y"))
        elif action == "type":
            computer_control._smart_type(data.get("text", ""))
            
        steps += 1
        time.sleep(1)
        
    return f"Aborted: Loop limit reached ({max_steps} steps) without achieving goal."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_gui_agent.py::test_execute_gui_action_loop_limit -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_gui_agent.py actions/gui_agent.py
git commit -m "feat: setup basic vision-action loop with failsafe"
```

---

### Task 2: Implement Real Screenshot and LLM Calls

**Files:**
- Modify: `actions/gui_agent.py`
- Modify: `core/prompt.txt`

**Interfaces:**
- Consumes: `actions.screen_processor._compress`, `google.genai.Client`
- Produces: Functional Vision LLM integration.

- [ ] **Step 1: Write the failing test for LLM integration**

```python
# tests/test_gui_agent.py
def test_execute_gui_action_success(monkeypatch):
    responses = [
        '{"action": "click", "x": 100, "y": 100, "reasoning": "clicking button"}',
        '{"action": "done", "reasoning": "finished"}'
    ]
    
    def mock_llm_call(*args, **kwargs):
        return responses.pop(0)
    
    monkeypatch.setattr("actions.gui_agent._call_vision_llm", mock_llm_call)
    monkeypatch.setattr("actions.gui_agent._take_screenshot", lambda: b"fake_bytes")
    monkeypatch.setattr("actions.computer_control._click", lambda x, y: "clicked")
    
    result = execute_gui_action("Click the button")
    assert "Goal achieved" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_gui_agent.py::test_execute_gui_action_success -v`
Expected: FAIL if logic has bugs, but should pass with our mock. To genuinely fail, we need to implement the real logic and test that the real logic can parse JSON correctly. We will proceed to implementation.

- [ ] **Step 3: Write real LLM and screenshot implementation**

```python
# actions/gui_agent.py
import json
import time
from google import genai
from google.genai import types as gtypes
from actions.computer_control import _get_api_key

def _take_screenshot() -> bytes:
    try:
        from PIL import ImageGrab
        import io
        img = ImageGrab.grab()
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()
    except ImportError:
        return b""

def _call_vision_llm(goal: str, screenshot_bytes: bytes) -> str:
    client = genai.Client(api_key=_get_api_key())
    prompt = f"""
    You are a precise GUI automation agent. Your goal is: {goal}
    Analyze the screenshot and output a JSON object with the next action.
    Format: {{"action": "click"|"type"|"done", "x": int, "y": int, "text": str, "reasoning": str}}
    """
    
    response = client.models.generate_content(
        model='gemini-3.1-high',
        contents=[
            prompt,
            gtypes.Part.from_bytes(data=screenshot_bytes, mime_type='image/png')
        ]
    )
    return response.text.strip('` \n').removeprefix('json')
```

- [ ] **Step 4: Update core prompt to include the new tool**

```text
# Modify core/prompt.txt - add under TOOL ROUTING:
- execute_gui_action: ONLY for visual UI automation. Use when the user asks to click things, search in specific non-standard tabs, or visually interact with desktop apps. Provide the goal string.
```

- [ ] **Step 5: Run tests to verify**

Run: `pytest tests/test_gui_agent.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add actions/gui_agent.py core/prompt.txt
git commit -m "feat: implement real screenshot and gemini-3.1-high vision calls"
```
