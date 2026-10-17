"""
Tests for Multi-Command Actions, Pacing Delays, and Interruptible Cancellation
"""
import time
import unittest
from src.core.models import SavedAction, ActionStep, CommandType
from src.engine.actions import ActionRunner


class TestActionRunner(unittest.TestCase):
    def test_action_execution_order(self):
        sent_log = []

        def _send(port, data):
            sent_log.append((port, list(data)))
            return True

        runner = ActionRunner(send_func=_send)

        action = SavedAction(
            id="test_act",
            name="Test Lead",
            steps=[
                ActionStep(
                    id="s1",
                    target_port_name="AmpPort",
                    channel=1,
                    command_type=CommandType.PROGRAM_CHANGE,
                    data1=10,
                    delay_ms=10,
                ),
                ActionStep(
                    id="s2",
                    target_port_name="DelayPort",
                    channel=2,
                    command_type=CommandType.CONTROL_CHANGE,
                    data1=102,
                    data2=127,
                    delay_ms=0,
                ),
            ],
        )

        connected = {"AmpPort": True, "DelayPort": True}
        res = runner.execute_action(action, connected)
        self.assertTrue(res["success"])
        self.assertFalse(res.get("cancelled", False))
        self.assertEqual(res["executed_steps"], 2)

        # Verify exact sent order
        self.assertEqual(len(sent_log), 2)
        self.assertEqual(sent_log[0], ("AmpPort", [0xC0, 10]))
        self.assertEqual(sent_log[1], ("DelayPort", [0xB1, 102, 127]))

    def test_action_interruptible_delay_cancellation(self):
        runner = ActionRunner(send_func=lambda p, d: True)

        action = SavedAction(
            id="test_cancel",
            name="Long Action",
            steps=[
                ActionStep(
                    id="s1",
                    target_port_name="TestPort",
                    channel=1,
                    command_type=CommandType.PROGRAM_CHANGE,
                    data1=1,
                    delay_ms=400,  # 400ms delay
                ),
                ActionStep(
                    id="s2",
                    target_port_name="TestPort",
                    channel=1,
                    command_type=CommandType.PROGRAM_CHANGE,
                    data1=2,
                    delay_ms=0,
                ),
            ],
        )

        connected = {"TestPort": True}

        # Cancel action 30ms into the 400ms delay
        import threading
        def _delayed_cancel():
            time.sleep(0.03)
            runner.cancel()

        t = threading.Thread(target=_delayed_cancel)
        t.start()

        t_start = time.perf_counter()
        res = runner.execute_action(action, connected)
        elapsed = time.perf_counter() - t_start

        # Should have aborted immediately without waiting out the full 400ms!
        self.assertFalse(res["success"])
        self.assertTrue(res.get("cancelled"))
        self.assertLess(elapsed, 0.20, f"Cancellation took too long: {elapsed:.3f}s")
        t.join()


if __name__ == "__main__":
    unittest.main()
