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
