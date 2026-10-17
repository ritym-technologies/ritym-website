"""Compatibility entry point for the dedicated PulseStage desktop window."""
from pathlib import Path
import sys
root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
if str(root) not in sys.path: sys.path.insert(0, str(root))
from src.launcher.native_desktop import main
if __name__ == "__main__": raise SystemExit(main())
