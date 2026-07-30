# MARK L Calendar Integration Spec

## 1. Overview
The goal is to implement a local, offline calendar system into MARK L that seamlessly supports both voice-driven operations (via Gemini) and manual UI operations (via PyQt6). It will integrate deeply with the Proactive 2.0 system to announce upcoming events verbally, while utilizing OS-level notifications as a fallback.

## 2. Architecture & Data Layer
- **Storage**: A local file at `memory/calendar.json`.
- **Format**: An array of JSON objects containing:
  - `id`: Unique identifier (UUID).
  - `title`: String description of the event.
  - `start_time`: ISO 8601 timestamp.
  - `end_time`: ISO 8601 timestamp (optional).
  - `description`: String for extra context (optional).
- **Justification**: Maintaining a local JSON file keeps the system lightweight and aligns perfectly with MARK L's existing persistent memory approach (e.g., `long_term.json`).

## 3. Core Components

### 3.1 `actions/calendar_manager.py`
This module will serve as the primary API for Gemini to interact with the calendar.
- `add_event(title, start_time, ...)`: Parses natural language dates into strict timestamps and appends to the JSON file.
- `get_upcoming_events(days)`: Retrieves events within a specified window to inform Gemini's context or briefing.
- `delete_event(event_id)`: Removes an event.

### 3.2 The Background Watcher
A new threaded watcher (similar to `system_monitor.py` or `background_monitor.py`) that reads `calendar.json` periodically (e.g., every 60 seconds).
- When an event is **X minutes away** (e.g., 10 minutes), it fires an event.
- **Action 1 (OS)**: Triggers `actions/reminder.py` to set an immediate OS-level notification.
- **Action 2 (Voice)**: Injects a high-priority prompt into `actions/proactive.py` (bypassing the standard 20-minute cooldown) to make Gemini announce the event out loud immediately if the app is active.

### 3.3 The UI Layer (`ui.py`)
A new interactive tab within the existing PyQt6 HUD.
- **Event List**: Displays a chronological list of upcoming events.
- **Add Event Form**: Provides a simple UI (Title, Date Picker, Time Picker) to manually add events without using voice.
- **Real-time Sync**: Updating the UI updates the JSON, and vice versa.

## 4. Scope and Limitations
- The calendar will not sync with external providers (Google, Apple, Outlook).
- It relies on the system clock being accurate.
- If the application is fully closed, the background watcher will not run, but any events that had an OS-reminder scheduled *in advance* might still trigger (depending on how `reminder.py` is utilized for future events vs immediate triggers).

## 5. Success Criteria
1. User can say "Schedule a meeting tomorrow at 3 PM" and it appears in the JSON.
2. User can open the UI tab and manually add an event, which is immediately visible to Gemini.
3. 10 minutes before an event, MARK L speaks the reminder aloud.
