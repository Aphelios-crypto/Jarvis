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
