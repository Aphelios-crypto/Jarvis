# Calendar Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a local, offline calendar system with voice (Gemini) and UI (PyQt6) integrations, plus a background watcher for proactive verbal reminders.

**Architecture:** A JSON-backed local datastore (`memory/calendar.json`) manipulated via `actions/calendar_manager.py`. Gemini interacts with it via new tool definitions. The PyQt6 UI reads it to render a Calendar tab. A new `calendar_watcher.py` threaded loop checks for events approaching in <= 10 minutes to trigger voice/OS alerts.

**Tech Stack:** Python 3.11+, PyQt6 (for UI), built-in `json` and `threading` libraries.

## Global Constraints

- No external cloud calendar syncing.
- Use `memory/calendar.json` for storage.
- All code must work cross-platform (Windows, macOS, Linux).

---

### Task 1: Calendar Manager and Storage

**Files:**
- Create: `actions/calendar_manager.py`
- Create: `tests/test_calendar_manager.py`

**Interfaces:**
- Produces: `add_event(title: str, start_time: str, end_time: str = "", description: str = "") -> str`
- Produces: `get_upcoming_events(days: int = 7) -> list`
- Produces: `delete_event(event_id: str) -> str`

- [ ] **Step 1: Write the failing tests**

```python
import os
import json
import unittest
from datetime import datetime, timedelta
from actions.calendar_manager import add_event, get_upcoming_events, delete_event, _get_calendar_file

class TestCalendarManager(unittest.TestCase):
    def setUp(self):
        self.test_file = _get_calendar_file()
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_add_and_get(self):
        start = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        res = add_event("Test Meeting", start)
        self.assertIn("Successfully added", res)
        
        events = get_upcoming_events(days=7)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["title"], "Test Meeting")
        
        delete_event(events[0]["id"])
        self.assertEqual(len(get_upcoming_events()), 0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests/test_calendar_manager.py`
Expected: FAIL with ModuleNotFoundError or ImportError

- [ ] **Step 3: Write minimal implementation**

```python
import json
import uuid
import os
from datetime import datetime, timedelta
from pathlib import Path

def _get_calendar_file():
    d = Path(__file__).resolve().parent.parent / "memory"
    d.mkdir(parents=True, exist_ok=True)
    return d / "calendar.json"

def _load_events():
    f = _get_calendar_file()
    if not f.exists():
        return []
    with open(f, "r", encoding="utf-8") as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []

def _save_events(events):
    with open(_get_calendar_file(), "w", encoding="utf-8") as file:
        json.dump(events, file, indent=4)

def add_event(title: str, start_time: str, end_time: str = "", description: str = "") -> str:
    try:
        datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return "Error: start_time must be in YYYY-MM-DDTHH:MM:SS format."
    
    events = _load_events()
    new_event = {
        "id": str(uuid.uuid4()),
        "title": title,
        "start_time": start_time,
        "end_time": end_time,
        "description": description
    }
    events.append(new_event)
    _save_events(events)
    return f"Successfully added event '{title}'."

def get_upcoming_events(days: int = 7) -> list:
    events = _load_events()
    now = datetime.now()
    limit = now + timedelta(days=days)
    upcoming = []
    
    for e in events:
        try:
            dt = datetime.strptime(e["start_time"], "%Y-%m-%dT%H:%M:%S")
            if now <= dt <= limit:
                upcoming.append(e)
        except ValueError:
            continue
            
    return sorted(upcoming, key=lambda x: x["start_time"])

def delete_event(event_id: str) -> str:
    events = _load_events()
    filtered = [e for e in events if e["id"] != event_id]
    if len(filtered) == len(events):
        return f"Event {event_id} not found."
    _save_events(filtered)
    return f"Deleted event {event_id}."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests/test_calendar_manager.py`
Expected: OK

- [ ] **Step 5: Commit**

```bash
git add tests/test_calendar_manager.py actions/calendar_manager.py
git commit -m "feat: core calendar storage and manager functions"
```

---

### Task 2: Gemini Tool Integration

**Files:**
- Modify: `core/prompt.txt`
- Modify: `main.py`

**Interfaces:**
- Consumes: `actions.calendar_manager.add_event`, `actions.calendar_manager.get_upcoming_events`

- [ ] **Step 1: Update Gemini System Prompt**

Add the tool definitions to `core/prompt.txt` (append to the tool descriptions section):
```text
- add_calendar_event: Use this to schedule a meeting or reminder. Provide title and start_time (YYYY-MM-DDTHH:MM:SS).
- get_calendar_events: Use this to check the user's upcoming schedule. Provide days (int).
```

- [ ] **Step 2: Update `main.py` Tool Dispatcher**

In `main.py`, locate the tool execution block (where `reminder`, `web_search` etc. are called) and add imports and routing for the calendar.

```python
# At the top with other imports:
from actions.calendar_manager import add_event, get_upcoming_events

# Inside the tool dispatch loop (e.g., in execute_tool or similar function):
if tool_name == "add_calendar_event":
    result = add_event(
        title=tool_args.get("title", "Event"),
        start_time=tool_args.get("start_time", ""),
        end_time=tool_args.get("end_time", ""),
        description=tool_args.get("description", "")
    )
elif tool_name == "get_calendar_events":
    days = tool_args.get("days", 7)
    events = get_upcoming_events(days=int(days))
    if not events:
        result = "No upcoming events."
    else:
        result = "Upcoming events:\n" + "\n".join([f"- {e['start_time']}: {e['title']}" for e in events])
```

*(Note: The exact injection point in `main.py` depends on how the `execute_tool` loop is written. The engineer should inspect `main.py` first to match the existing pattern).*

- [ ] **Step 3: Commit**

```bash
git add core/prompt.txt main.py
git commit -m "feat: register calendar tools with Gemini prompt and main loop"
```

---

### Task 3: The Background Watcher

**Files:**
- Create: `actions/calendar_watcher.py`

**Interfaces:**
- Consumes: `actions.calendar_manager.get_upcoming_events`
- Produces: `CalendarWatcher` class that runs on a background thread.

- [ ] **Step 1: Write the Watcher Implementation**

```python
import threading
import time
from datetime import datetime
from actions.calendar_manager import get_upcoming_events

class CalendarWatcher:
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.thread = None
        self._notified_events = set()
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        
    def _watch_loop(self):
        while self.running:
            events = get_upcoming_events(days=1)
            now = datetime.now()
            
            for event in events:
                event_id = event["id"]
                if event_id in self._notified_events:
                    continue
                    
                try:
                    dt = datetime.strptime(event["start_time"], "%Y-%m-%dT%H:%M:%S")
                    diff = (dt - now).total_seconds()
                    # Trigger if event is between 0 and 10 minutes away
                    if 0 < diff <= 600:
                        self.callback(event)
                        self._notified_events.add(event_id)
                except ValueError:
                    pass
                    
            time.sleep(60) # check every minute
```

- [ ] **Step 2: Integrate into `main.py`**

In `main.py`, instantiate the watcher at startup, and define the callback to inject a proactive message.

```python
# In main.py
from actions.calendar_watcher import CalendarWatcher

def handle_calendar_alert(event):
    msg = f"[URGENT CALENDAR ALERT] The user's event '{event['title']}' is starting in less than 10 minutes! Inform the user immediately out loud."
    # Assuming there's a queue or direct way to send messages to the Gemini loop:
    # prompt_queue.put(msg) 
    # (The engineer must adapt this to main.py's actual architecture for proactive/injected messages).

calendar_watcher = CalendarWatcher(callback=handle_calendar_alert)
calendar_watcher.start()
```

- [ ] **Step 3: Commit**

```bash
git add actions/calendar_watcher.py main.py
git commit -m "feat: background calendar watcher for immediate 10-minute alerts"
```

---

### Task 4: The UI Tab

**Files:**
- Modify: `ui.py`

**Interfaces:**
- Consumes: `memory/calendar.json` directly or via `calendar_manager.py`.

- [ ] **Step 1: Add a new Calendar Tab to the PyQt6 layout**

Modify `ui.py` to import `calendar_manager` and add a new `QWidget` tab alongside the existing log/settings panels.

```python
# Inside ui.py, locate the QTabWidget (or main layout) and add:
from PyQt6.QtWidgets import QVBoxLayout, QListWidget, QPushButton, QWidget
from actions.calendar_manager import get_upcoming_events

# Inside the Main Window init:
self.calendar_tab = QWidget()
cal_layout = QVBoxLayout()
self.event_list = QListWidget()
cal_layout.addWidget(self.event_list)

refresh_btn = QPushButton("Refresh Events")
refresh_btn.clicked.connect(self.refresh_calendar)
cal_layout.addWidget(refresh_btn)

self.calendar_tab.setLayout(cal_layout)
# Assume self.tabs is a QTabWidget:
# self.tabs.addTab(self.calendar_tab, "Calendar")

def refresh_calendar(self):
    self.event_list.clear()
    events = get_upcoming_events()
    for e in events:
        self.event_list.addItem(f"{e['start_time']} - {e['title']}")
```

*(Note: The engineer must fit this into the specific UI structure established in `ui.py` and ensure thread-safety if needed).*

- [ ] **Step 2: Commit**

```bash
git add ui.py
git commit -m "feat: add calendar view to PyQt6 HUD"
```
