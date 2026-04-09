"""
Entry point for the Brain Tumour AI desktop application.

Run with:
    python gui/main.py
    python -m gui.main
    tumor-detect-gui          # if installed via pip
"""

import sys
import logging
from pathlib import Path

# Ensure project root is importable regardless of cwd
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
    except ImportError:
        print(
            "PyQt6 is required.\n"
            "Install with:  pip install PyQt6\n"
            "Or:            pip install 'tumor-detection-segmentation[gui]'"
        )
        sys.exit(1)

    from gui.app import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Brain Tumour AI")
    app.setOrganizationName("tumor-detection")

    # Consistent dark palette handled via stylesheets in app.py
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
