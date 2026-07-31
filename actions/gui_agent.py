import json
import time

from google import genai
from google.genai import types as gtypes
from actions.computer_control import _get_api_key

def _call_vision_llm(goal: str, screenshot_bytes: bytes) -> str:
    client = genai.Client(api_key=_get_api_key())
    prompt = f"""
    You are a precise GUI automation agent. Your goal is: {goal}
    Analyze the screenshot and output a JSON object with the next action.
    Format: {{"action": "click"|"type"|"done", "x": int, "y": int, "text": str, "reasoning": str}}
    """
    
    response = client.models.generate_content(
        model='gemini-3.1-pro',
        contents=[
            prompt,
            gtypes.Part.from_bytes(data=screenshot_bytes, mime_type='image/png')
        ]
    )
    # The output might have markdown formatting like ```json ... ```
    text = response.text.strip('` \n')
    if text.startswith('json\n'):
        text = text[5:]
    elif text.startswith('json'):
        text = text[4:]
    return text.strip()

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
