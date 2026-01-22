# PolicyHub Development Guide

Development context for PolicyHub, a Windows desktop application for policy and procedure lifecycle management.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| UI Framework | CustomTkinter 5.2+ |
| Tables | tksheet 7.0+ |
| Database | SQLite3 (WAL mode) |
| Password Hashing | bcrypt |
| PDF Reports | ReportLab |
| Excel Reports | openpyxl |
| Packaging | PyInstaller |

## Architecture

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

## Project Structure

```
PolicyHub/
├── main.py                    # Entry point
├── app/
│   ├── application.py         # Main app class (startup flow)
│   ├── constants.py           # Enums: DocumentType, Status, Role
│   └── theme.py               # Colors, Typography, Spacing
├── core/
│   ├── config.py              # LocalConfig + ConfigManager
│   ├── database.py            # DatabaseManager + schema SQL
│   ├── session.py             # UserSession + SessionManager
│   └── permissions.py         # Permission enum + RBAC
├── models/                    # Dataclasses (User, Document, etc.)
├── services/                  # Business logic layer
│   ├── auth_service.py        # Login, password hashing
│   ├── user_service.py        # User CRUD
│   ├── document_service.py    # Document CRUD with audit logging
│   ├── category_service.py    # Category CRUD
│   ├── history_service.py     # Audit trail logging
│   ├── attachment_service.py  # File attachment management
│   ├── link_service.py        # Document linking
│   ├── settings_service.py    # Application settings CRUD
│   └── report_service.py      # Report generation
├── views/                     # UI screens
│   ├── base_view.py           # BaseView, CenteredView, ScrollableView
│   ├── main_view.py           # Main app with sidebar navigation
│   ├── dashboard_view.py      # Statistics and attention items
│   ├── register_view.py       # Document table with filtering
│   ├── document_detail_view.py # Document details with tabs
│   ├── settings_view.py       # Settings container
│   ├── reports_view.py        # Report generation UI
│   └── settings/              # Settings sub-views
├── dialogs/                   # Modal dialogs
├── components/                # Reusable UI components
├── reports/                   # PDF/Excel generators
├── utils/                     # Helper functions
└── tests/                     # Pytest test suite
```

## Key Patterns

### Singleton Pattern

Used for managers requiring global access:

```python
from core.session import SessionManager
from core.config import ConfigManager
from core.database import DatabaseManager

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
    pass
```

### View Structure

All views extend `BaseView`:

```python
from views.base_view import BaseView

class MyView(BaseView):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build_ui()

    def on_show(self):
        super().on_show()
        self._refresh_data()

    def on_hide(self):
        super().on_hide()
```

### Theme Constants

Always use theme constants from `app/theme.py`:

```python
from app.theme import COLORS, TYPOGRAPHY, SPACING, configure_button_style

button = ctk.CTkButton(parent, text="Save")
configure_button_style(button, "primary")  # or "secondary", "danger"
```

## Database

SQLite with network share support:

- **WAL mode** for concurrent access
- **30 second timeout** for busy handling
- **Foreign keys enabled**

### Schema Tables

| Table | Purpose |
|-------|---------|
| users | User accounts |
| documents | Policy/procedure metadata |
| attachments | File storage tracking |
| document_links | Document relationships |
| document_history | Audit trail |
| categories | Document classification |
| settings | Application configuration |

### Database Operations

```python
from core.database import DatabaseManager

db = DatabaseManager.get_instance()

# Fetch single row
row = db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))

# Fetch all rows
rows = db.fetch_all("SELECT * FROM documents WHERE status = ?", ("ACTIVE",))

# Transaction context manager
with db.get_connection() as conn:
    conn.execute("INSERT INTO ...", params)
```

## Running Commands

```bash
# Development
python main.py

# Tests
pytest
pytest --cov=. --cov-report=html

# Build executable
build.bat
```

## Design Guidelines

See `UIUX.md` for visual design specifications:

- **Primary Color:** #2D3E50 (Ink Blue)
- **Secondary Color:** #E6E2DA (Warm Grey-Beige)
- **Background:** #F9FAFB
- **Font:** Segoe UI (system font)
- **Light mode only** (no dark theme)

## Development Notes

- **Dates stored as ISO 8601** — format at display time
- **UUIDs for all IDs** — use `utils.files.generate_uuid()`
- **Network share support** — 30s timeout, WAL mode
- **Password hashing** — bcrypt with automatic salt

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
