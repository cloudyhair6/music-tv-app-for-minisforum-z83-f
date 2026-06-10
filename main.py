"""MiniPC - A fullscreen TV-like media center for Windows.

Automatically installs missing Python dependencies on first run.
"""
import sys
import os
import subprocess
import importlib

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Auto-install missing packages
# ---------------------------------------------------------------------------

# Map: import name -> pip package name
_REQUIRED_PACKAGES = {
    "PySide6": "PySide6",
    "pycaw": "pycaw",
    "comtypes": "comtypes",
    "screen_brightness_control": "screen-brightness-control",
    "win32api": "pywin32",
}


def _ensure_dependencies() -> None:
    """Check for missing packages and install them automatically."""
    missing: list[str] = []

    for import_name, pip_name in _REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    print(f"[MiniPC] Installing missing packages: {', '.join(missing)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", *missing],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        print("[MiniPC] All packages installed successfully.")

        # pywin32 needs a post-install step to register pywintypes DLL
        if "pywin32" in missing:
            try:
                import pywin32_postinstall
                pywin32_postinstall.install()
                print("[MiniPC] pywin32 post-install completed.")
            except Exception:
                # Try alternative: run the post-install script directly
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pywin32_postinstall", "-install"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                    )
                except Exception:
                    print("[MiniPC] Note: pywin32 post-install may need admin rights.")

    except subprocess.CalledProcessError as e:
        print(f"[MiniPC] Failed to install packages: {e}")
        print("[MiniPC] Try running: pip install " + " ".join(missing))
        sys.exit(1)

    # Reload so the rest of the script can import them
    importlib.invalidate_caches()


# Run auto-install before any PySide6 imports
_ensure_dependencies()

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QPalette, QColor  # noqa: E402

from styles.theme import Colors, get_global_stylesheet  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


def create_dark_palette() -> QPalette:
    """Create a dark color palette for the application."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.BG_CARD_SOLID))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Link, QColor(Colors.ACCENT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.TEXT_PRIMARY))
    return palette


def main():
    """Application entry point."""
    # Enable high DPI scaling
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("MiniPC")
    app.setApplicationDisplayName("MiniPC Media Center")

    # Apply dark theme
    app.setPalette(create_dark_palette())
    app.setStyleSheet(get_global_stylesheet())

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
