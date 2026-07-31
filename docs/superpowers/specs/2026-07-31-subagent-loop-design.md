# Subagent Loop Integration Design

## Overview
We are adding a native subagent loop to Jarvis. This will transform Jarvis from a single-shot action executor into an autonomous agent capable of multi-step reasoning, self-correction, and background task execution. 

## Architecture: The Subagent Loop
We will create `actions/subagent.py` to handle the recursive tool-calling loop.

### 1. `invoke_subagent` Tool
This tool will be exposed to the main Jarvis brain. When Jarvis receives a complex task (e.g., "build a python script", "debug this error", "research and write a report"), he will call this tool, passing the user's objective as a string.

### 2. The Execution Environment
The subagent will be powered exclusively by **Gemini 3.1 Pro High** for maximum reasoning capabilities. It will use the Google GenAI SDK's built-in `tools` and `function_calling` features.

We will expose a precise subset of tools to the subagent:
- `read_file(path: str)` -> Reads code and text files.
- `write_file(path: str, content: str)` -> Creates new files and writes complete code.
- `edit_file(path: str, target: str, replacement: str)` -> Modifies existing code without rewriting the whole file.
- `run_command(command: str, cwd: str)` -> Executes terminal commands (e.g., running tests, installing packages, checking git status).
- `list_directory(path: str)` -> Explores the filesystem.

### 3. The Loop Mechanism
1. The subagent is prompted with the user's objective.
2. It responds with a `function_call` (e.g., `run_command("python test.py")`).
3. The Python execution wrapper runs the command and returns the output to the subagent.
4. The subagent reads the output (e.g., sees a syntax error), and makes another `function_call` to fix the code.
5. This loop repeats until the subagent decides the goal is fully achieved. It then returns a final `text` response.

### 4. Safety Guardrails
- **Turn Cap:** The loop will be hard-capped at 30 iterations to prevent infinite looping and excessive API costs.
- **Timeouts:** All terminal commands will have strict timeout limits to prevent blocking execution.

## Integration
- Add `invoke_subagent` to `core/prompt.txt` so Jarvis knows when and how to dispatch subagents.
