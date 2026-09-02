import unittest

from src.fieldservice_mail import needs_follow_up


class FollowUpDecisionTest(unittest.TestCase):
    def test_bounce_requires_a_technician_follow_up(self) -> None:
        self.assertTrue(needs_follow_up([{"event": "bounce"}]))
        self.assertFalse(needs_follow_up([{"event": "open"}]))


if __name__ == "__main__":
    unittest.main()
