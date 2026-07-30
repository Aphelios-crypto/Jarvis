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
            try:
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
            except Exception as e:
                print(f"[CalendarWatcher] Error: {e}")
                
            time.sleep(60) # check every minute
