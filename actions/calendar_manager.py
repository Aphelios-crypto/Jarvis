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
