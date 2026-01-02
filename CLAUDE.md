# PolicyHub Development Guide

This document provides context for developing PolicyHub, a Windows desktop application for policy and procedure lifecycle management.

## Tech Stack

- **Language:** Python 3.11+
- **UI Framework:** CustomTkinter 5.2+ (modern themed Tkinter)
- **Tables:** tksheet 7.0+
- **Database:** SQLite3 (built-in)
- **Password Hashing:** bcrypt
- **Reports:** ReportLab (PDF), openpyxl (Excel)
- **Packaging:** PyInstaller

## Architecture Overview

PolicyHub uses a layered architecture:

```
┌─────────────────────────────────────┐
│           Views (UI)                │  CustomTkinter frames
├─────────────────────────────────────┤
│         Services (Business)         │  Auth, User, Document logic
├─────────────────────────────────────┤
│           Models (Data)             │  Dataclasses
├─────────────────────────────────────┤
│         Core (Infrastructure)       │  Database, Session, Config
└─────────────────────────────────────┘
```

## Key Patterns

### Singleton Pattern
Used for managers that need global access:
- `ConfigManager` - Local configuration
- `SessionManager` - Current user session
- `DatabaseManager` - Database connections

```python
# Get instance
session = SessionManager.get_instance()
if session.is_authenticated:
    user = session.current_user
```

### Service Layer
Business logic is encapsulated in services:
```python
from services.auth_service import AuthService
from core.database import DatabaseManager

db = DatabaseManager.get_instance()
auth = AuthService(db)
session = auth.login(username, password)
```

### Permission Decorator
Role-based access control:
```python
from core.permissions import Permission, require_permission

@require_permission(Permission.MANAGE_USERS)
def create_user(data):
    # Only admins can reach here
    ...
```

## Database

SQLite with network share support:
- **WAL mode** for concurrent access
- **30 second timeout** for busy handling
- **Foreign keys enabled**

Schema includes 7 tables:
- `users` - User accounts
- `documents` - Policy/procedure metadata
- `attachments` - File storage tracking
- `document_links` - Relationships
- `document_history` - Audit trail
- `categories` - Document classification
- `settings` - App configuration

### Working with Database

```python
from core.database import DatabaseManager

db = DatabaseManager.get_instance()

# Fetch single row
row = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))

# Fetch all rows
rows = db.fetch_all("SELECT * FROM documents WHERE status = ?", ("ACTIVE",))

# Use context manager for transactions
with db.get_connection() as conn:
    conn.execute("INSERT INTO ...", params)
```

## CustomTkinter Patterns

### View Structure
All views extend `BaseView`:
```python
from views.base_view import BaseView

class MyView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build_ui()

    def on_show(self):
        # Called when view becomes visible
        super().on_show()
        self._refresh_data()

    def on_hide(self):
        # Called when view is hidden
        super().on_hide()
```

### Styling
Use theme constants for consistency:
```python
from app.theme import COLORS, TYPOGRAPHY, SPACING, configure_button_style

button = ctk.CTkButton(parent, text="Save")
configure_button_style(button, "primary")  # or "secondary", "danger"
```

### View Switching
The main application handles view switching:
```python
# In PolicyHubApp
def _show_login_view(self):
    self._clear_container()
    view = LoginView(self.container, self, self.db, ...)
    view.pack(fill="both", expand=True)
    self.current_view = view
    view.on_show()
```

## File Organization

```
policyhub/
├── main.py                    # Entry point
├── app/
│   ├── application.py         # Main app class (startup flow)
│   ├── constants.py           # Enums: DocumentType, Status, Role, etc.
│   └── theme.py               # COLORS, TYPOGRAPHY, SPACING dataclasses
├── core/
│   ├── config.py              # LocalConfig + ConfigManager
│   ├── database.py            # DatabaseManager + schema SQL
│   ├── session.py             # UserSession + SessionManager
│   └── permissions.py         # Permission enum + RBAC
├── models/
│   ├── user.py                # User dataclass
│   ├── document.py            # Document dataclass
│   ├── category.py            # Category dataclass
│   ├── attachment.py          # Attachment dataclass
│   ├── history.py             # HistoryEntry dataclass
│   └── link.py                # DocumentLink dataclass
├── services/
│   ├── auth_service.py        # Login, password hashing
│   ├── user_service.py        # User CRUD
│   ├── document_service.py    # Document CRUD with audit logging
│   ├── category_service.py    # Category CRUD
│   ├── history_service.py     # Audit trail logging
│   ├── attachment_service.py  # File attachment management
│   └── link_service.py        # Document linking
├── components/
│   ├── status_badge.py        # Status badge component
│   ├── stat_card.py           # Statistics card component
│   └── filter_bar.py          # Filter bar with dropdowns
├── dialogs/
│   ├── base_dialog.py         # Base modal dialog class
│   ├── confirm_dialog.py      # Yes/No confirmation dialog
│   ├── document_dialog.py     # Add/Edit document form
│   ├── upload_dialog.py       # File upload dialog
│   └── link_dialog.py         # Document linking dialog
├── views/
│   ├── base_view.py           # BaseView, CenteredView, ScrollableView
│   ├── setup_view.py          # Folder selection wizard
│   ├── admin_creation_view.py # First admin setup
│   ├── login_view.py          # Authentication screen
│   ├── main_view.py           # Main app with sidebar + view switching
│   ├── dashboard_view.py      # Statistics and attention items
│   ├── register_view.py       # Document table with filtering
│   └── document_detail_view.py # Full document details with tabs
├── utils/
│   ├── dates.py               # Date formatting/calculations
│   ├── validators.py          # Input validation
│   └── files.py               # File path utilities
└── tests/
    ├── conftest.py            # Pytest fixtures
    ├── test_auth.py           # Auth service tests
    ├── test_config.py         # Config manager tests
    ├── test_database.py       # Database tests
    ├── test_document_service.py # Document service tests
    ├── test_category_service.py # Category service tests
    ├── test_history_service.py  # History service tests
    ├── test_attachment_service.py # Attachment service tests
    └── test_link_service.py   # Link service tests
```

## Running the Application

```bash
# Development
python main.py

# Tests
pytest
pytest --cov=. --cov-report=html

# Build executable
pyinstaller --name PolicyHub --onefile --windowed main.py
```

## Implementation Status

### Completed (Phase 1 & 2)
- [x] Project structure and dependencies
- [x] Theme configuration (colors, fonts, spacing)
- [x] Constants and enums
- [x] Local config management
- [x] Database schema and manager
- [x] Session management
- [x] Permission system
- [x] All data models
- [x] Auth service (login, password hashing)
- [x] User service (CRUD)
- [x] Setup wizard view
- [x] Admin creation view
- [x] Login view
- [x] Main view (placeholder)
- [x] Test suite

### Completed (Phase 3 & 4)
- [x] History service (audit logging)
- [x] Category service (CRUD)
- [x] Document service (CRUD with auto-logging)
- [x] UI Components (StatusBadge, StatCard, FilterBar)
- [x] Dialog system (BaseDialog, ConfirmDialog, DocumentDialog)
- [x] Dashboard view with statistics
- [x] Document register view with filtering
- [x] Document detail view with tabs
- [x] MainView with view switching
- [x] Add/Edit document dialog
- [x] Mark as reviewed workflow

### Completed (Phase 5 - Attachments & Links)
- [x] AttachmentService (upload, version tracking, validation)
- [x] UploadDialog (file browser, validation, version label)
- [x] Attachments Tab UI (list, upload, open, delete)
- [x] LinkService (create, delete, bidirectional relationships)
- [x] LinkDialog (search, link type selection)
- [x] Links Tab UI (list, add, navigate, remove)
- [x] History logging for attachments and links
- [x] Service tests (111 total tests)

### Pending (Phase 6+)
- [ ] Reports generation (PDF/Excel)
- [ ] Settings views (categories, company settings)
- [ ] Full user management UI
- [ ] Audit log viewer

## Common Tasks

### Add a New View
1. Create file in `views/`
2. Extend `BaseView` or `CenteredView`
3. Implement `_build_ui()` method
4. Override `on_show()` for data refresh

### Add a New Service
1. Create file in `services/`
2. Accept `DatabaseManager` in `__init__`
3. Use `@require_permission` for protected methods

### Add Database Table
1. Add CREATE TABLE in `core/database.py` SCHEMA_SQL
2. Create model in `models/`
3. Create service in `services/`

### Update Theme
Edit `app/theme.py`:
- `Colors` dataclass for colors
- `Typography` dataclass for fonts
- `Spacing` dataclass for layout
- Helper functions for component styling

## Notes

- **Light mode only** - no dark theme per PRD requirements
- **Dates stored as ISO 8601** - format at display time
- **UUIDs for all IDs** - use `utils.files.generate_uuid()`
- **Network share support** - 30s timeout, WAL mode
- **Password hashing** - bcrypt with automatic salt
