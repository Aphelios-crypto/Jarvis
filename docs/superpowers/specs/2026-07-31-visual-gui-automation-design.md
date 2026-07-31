# Visual GUI Automation Design

## Overview
The goal is to make Jarvis highly precise and capable of interacting with any application on the user's computer visually, exactly as a human would. This solves issues like Jarvis failing to interact with specific tabs (e.g., searching Facebook) by allowing him to "see" the screen and manipulate the mouse and keyboard directly.

## Architecture: The Vision-Action Loop
We will introduce a new specialized agent, the `gui_agent`, which implements a continuous vision-action loop. 

### Core Components
1. **Perception (Vision):**
   - The agent takes a full-screen screenshot using `mss` or `pyautogui`.
   - The screenshot is passed to a multimodal LLM (Gemini 3.1 High) along with the user's current goal.

2. **Decision (LLM Reasoning):**
   - The Vision LLM analyzes the screenshot to locate the UI elements required to progress toward the goal.
   - It outputs specific coordinates (X, Y) and actions (e.g., `click(x, y)`, `type("text")`, `done()`).

3. **Action (Execution):**
   - The agent parses the LLM's chosen action and executes it using the primitives already defined in `actions/computer_control.py` (which uses `pyautogui`).

4. **Verification (Looping):**
   - After executing an action, the agent waits briefly for the UI to update, takes a new screenshot, and repeats the cycle until the LLM determines the goal is complete.

## Component Design

### 1. `actions/gui_agent.py` [NEW]
This file will contain the main `execute_gui_action(goal: str)` function.
- Will handle the loop state.
- Will format the prompts for the Vision LLM, instructing it to output JSON containing the next action.
- Will manage error handling (e.g., if the LLM gets stuck in a loop, abort after N steps).

### 2. Prompting Strategy
The system prompt for the `gui_agent` will instruct the model to act as a precise UI automation tool. 
- Input: Current screenshot, Goal, Previous actions taken.
- Output: Structured JSON (e.g., `{"action": "click", "x": 500, "y": 200, "reasoning": "Clicking the search bar"}`).

### 3. Integration with `core/prompt.txt`
We will update the core Jarvis routing prompt to include the new capability:
- **Tool Added:** `execute_gui_action`
- **Trigger:** When the user asks to manipulate the screen, click on things, search within specific non-standard tabs, or explicitly interact with desktop apps visually.

## Error Handling & Safety
- **Failsafe:** The `pyautogui.FAILSAFE` feature (moving the mouse to the corner of the screen to abort) will be emphasized.
- **Max Steps:** The loop will be hard-capped at a reasonable number of steps (e.g., 10-15) to prevent infinite loops if the agent gets confused.

## Testing Strategy
- Test finding and clicking a specific icon on the desktop.
- Test the original failing scenario: "search in my facebook tab for Aeron Rae Agbuya" to ensure the agent can visually locate the search bar, click it, and type the query.
