"""
Widget Sidebar - Windows Clipboard Manager
Main entry point for the application

Version: 2.0.1
Author: Widget Sidebar Team
License: MIT
"""

import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtWebEngineWidgets import QWebEngineView  # Necesario para inicializar QtWebEngine

# Fix encoding for Windows console
if sys.platform == 'win32' and sys.stdout:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup logging
def setup_logging():
    """Configure detailed logging to file"""
    log_file = Path("widget_sidebar_error.log")

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("="*70)
    logger.info(f"Widget Sidebar v2.0.1 - Session started at {datetime.now()}")
    logger.info("="*70)
    return logger

# Global exception handler
def exception_hook(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = logging.getLogger(__name__)
    logger.critical("Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback))

    # Show error dialog
    error_msg = f"Error crítico:\n{exc_type.__name__}: {exc_value}\n\nRevisa widget_sidebar_error.log para más detalles."
    QMessageBox.critical(None, "Error Fatal", error_msg)

# Install exception hook
sys.excepthook = exception_hook

# Setup logging
logger = setup_logging()

# Handle path for both script and bundled exe
if not getattr(sys, 'frozen', False):
    # Add src directory to Python path when running as a script
    src_path = Path(__file__).parent / 'src'
    sys.path.insert(0, str(src_path))

from controllers.main_controller import MainController
from views.main_window import MainWindow
from core.auth_manager import AuthManager
from core.session_manager import SessionManager
from views.first_time_wizard import FirstTimeWizard
from views.login_dialog import LoginDialog


def get_app_dir() -> Path:
    """
    Get the application directory path

    Returns the directory where the executable or script is located
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent


def ensure_database(db_path: Path) -> None:
    """
    Ensure database exists, create if necessary

    Args:
        db_path: Path to the database file
    """
    if not db_path.exists():
        print(f"Database not found, creating new database at {db_path}...")
        # Import here to avoid circular imports
        from database.db_manager import DBManager

        # Create database (will auto-initialize with schema)
        db = DBManager(str(db_path))
        db.close()
        print("Database created successfully")


def authenticate() -> bool:
    """
    Handle authentication flow

    Returns:
        True if authenticated successfully, False if user cancelled
    """
    logger.info("Starting authentication flow...")

    auth_manager = AuthManager()
    session_manager = SessionManager()

    # Check if valid session exists
    if session_manager.validate_session():
        logger.info("Valid session found - skipping login")
        return True

    # Check if first time
    if auth_manager.is_first_time():
        logger.info("First time execution - showing FirstTimeWizard")
        wizard = FirstTimeWizard()
        result = wizard.exec()

        if result:
            logger.info("Password created successfully")
            return True
        else:
            logger.info("User cancelled first time setup")
            return False

    # Show login dialog
    logger.info("No valid session - showing LoginDialog")
    login = LoginDialog()
    result = login.exec()

    if result:
        logger.info("Login successful")
        return True
    else:
        logger.info("User cancelled login")
        return False


def main():
    """Main entry point for Widget Sidebar application"""
    try:
        logger.info("=" * 60)
        logger.info("Widget Sidebar v2.0.1 - SQLite Edition")
        logger.info("=" * 60)

        # Get application directory
        logger.info("Getting application directory...")
        app_dir = get_app_dir()
        logger.info(f"App directory: {app_dir}")

        db_path = app_dir / "widget_sidebar.db"
        logger.info(f"Database path: {db_path}")

        # Ensure database exists
        logger.info("Ensuring database exists...")
        ensure_database(db_path)
        logger.info("Database ready")

        # Initialize PyQt6 application
        logger.info("Initializing PyQt6 application...")
        app = QApplication(sys.argv)
        app.setApplicationName("Widget Sidebar")
        logger.info("PyQt6 application initialized")

        # Authentication flow
        logger.info("=" * 60)
        logger.info("AUTHENTICATION")
        logger.info("=" * 60)
        if not authenticate():
            logger.info("Authentication cancelled - exiting application")
            sys.exit(0)
        logger.info("Authentication successful")
        logger.info("=" * 60)

        # Initialize main controller with database path
        logger.info("Initializing MVC architecture...")
        controller = MainController()
        logger.info("MainController initialized")

        # Create main window with controller
        logger.info("Creating main window...")
        window = MainWindow(controller)
        logger.info("MainWindow created")

        # Set controller's main_window reference for bidirectional communication
        controller.main_window = window
        logger.info("Controller main_window reference set")

        # Set main_window reference in browser_manager for positioning
        controller.browser_manager.set_main_window(window)
        logger.info("Browser manager main_window reference set")

        # Load categories into sidebar
        logger.info("Loading categories into UI...")
        categories = controller.get_categories()
        logger.info(f"Loaded {len(categories)} categories")

        window.load_categories(categories)
        logger.info("Categories loaded into sidebar")

        # Show window
        logger.info("Showing window...")
        window.show()
        logger.info("Window shown")

        logger.info(f"[OK] Loaded {len(categories)} categories from SQLite")
        logger.info("[OK] UI fully functional")
        logger.info("Application ready!")
        logger.info("=" * 60)

        # Start event loop
        logger.info("Starting Qt event loop...")
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code)

    except Exception as e:
        logger.critical(f"Fatal error in main(): {e}", exc_info=True)

        # Show error dialog
        error_msg = f"Error fatal al iniciar:\n{str(e)}\n\nRevisa widget_sidebar_error.log para más detalles."
        try:
            QMessageBox.critical(None, "Error Fatal", error_msg)
        except:
            print(error_msg)

        sys.exit(1)


if __name__ == '__main__':
    main()
