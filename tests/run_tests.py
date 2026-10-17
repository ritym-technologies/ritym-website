"""
Comprehensive Automated Test Suite Runner
"""
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_all():
    print("=" * 65)
    print(" RUNNING PULSESTAGE MIDI AUTOMATED TEST SUITE")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(PROJECT_ROOT / "tests"), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 65)
    if result.wasSuccessful():
        print(f" ALL {result.testsRun} TESTS PASSED SUCCESSFULLY.")
        print("=" * 65)
        return 0
    else:
        print(f" TESTS FAILED. Failures: {len(result.failures)}, Errors: {len(result.errors)}")
        print("=" * 65)
        return 1


if __name__ == "__main__":
    sys.exit(run_all())
