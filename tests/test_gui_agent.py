import pytest
from actions.gui_agent import execute_gui_action

def test_execute_gui_action_loop_limit(monkeypatch):
    def mock_llm_call(*args, **kwargs):
        return '{"action": "click", "x": 100, "y": 100, "reasoning": "mock"}'
    
    monkeypatch.setattr("actions.gui_agent._call_vision_llm", mock_llm_call)
    
    monkeypatch.setattr("actions.gui_agent._take_screenshot", lambda: b"fake_bytes")
    monkeypatch.setattr("actions.computer_control._click", lambda x, y: "clicked")
    
    result = execute_gui_action("Do something impossible")
    assert "loop limit reached" in result.lower() or "aborted" in result.lower()

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
