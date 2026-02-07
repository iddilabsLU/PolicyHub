"""
PolicyHub - Policy & Procedure Lifecycle Manager

Entry point for the PolicyHub desktop application.

Usage:
    python main.py

For development, ensure you have installed dependencies:
    pip install -r requirements.txt
"""

import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


def setup_logging() -> None:
    """Configure logging for the application."""
    # Create logs directory in local app data
    log_dir = Path.home() / "AppData" / "Local" / "PolicyHub" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "policyhub.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    """Main entry point for PolicyHub."""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        # Enable high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Create the application
        app = QApplication(sys.argv)

        # Set application metadata
        app.setApplicationName("PolicyHub")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("IddiLabs")

        # Set default font
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        # Import and create the main window
        from app.application import PolicyHubApp

        window = PolicyHubApp()
        window.run()

        # Run the event loop
        sys.exit(app.exec())

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        # Show error dialog
        try:
            error_app = QApplication.instance()
            if error_app is None:
                error_app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "PolicyHub Error",
                f"An unexpected error occurred:\n\n{str(e)}\n\nCheck the log file for details.",
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
