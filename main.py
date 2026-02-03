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

import customtkinter as ctk


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
        # Configure CustomTkinter
        ctk.set_appearance_mode("light")  # Light mode only
        ctk.set_default_color_theme("blue")  # Base theme (we override most colors)

        # Import and run the application
        from app.application import PolicyHubApp

        app = PolicyHubApp()
        app.run()

    except Exception as e:
        # Ignore "application has been destroyed" errors - these are expected
        # when the user closes the app early (e.g., cancels database selection)
        error_msg = str(e).lower()
        if "application has been destroyed" in error_msg:
            logger.info("Application closed by user")
            sys.exit(0)

        logger.exception(f"Fatal error: {e}")
        # Show error dialog
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror(
                "PolicyHub Error",
                f"An unexpected error occurred:\n\n{str(e)}\n\nCheck the log file for details.",
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
