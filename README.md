# PolicyHub

**Policy & Procedure Lifecycle Manager**

A native Windows desktop application for managing policies and procedures in regulated financial entities. Designed for Luxembourg PSFs, fund administrators, and compliance teams.

## Features

- **Document Register** - Central tracking of all policies, procedures, manuals, and registers
- **Review Management** - Track review dates with visual status indicators (overdue, due soon, on track)
- **Multi-User Access** - Role-based permissions (Admin, Editor, Viewer) via shared network folder
- **Document Links** - Map procedures to implementing policies
- **Audit Trail** - Complete history of all changes
- **Attachments** - Store actual policy documents alongside metadata
- **Reports** - Generate PDF and Excel exports

## System Requirements

- **Operating System:** Windows 10 or 11
- **Python:** 3.11 or higher (for running from source)
- **Network:** Access to shared folder for multi-user deployment

## Installation

### Option 1: Run from Source (Development)

1. **Clone or download the project:**
   ```bash
   git clone <repository-url>
   cd policyhub
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

### Option 2: Build Standalone Executable

1. **Install dependencies including PyInstaller:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the executable:**
   ```bash
   pyinstaller --name PolicyHub --onefile --windowed --icon=assets/icons/app_icon.ico main.py
   ```

3. **Find the executable in `dist/PolicyHub.exe`**

## First-Time Setup

1. **Launch PolicyHub**
2. **Select Shared Folder:**
   - Enter the path to your shared network folder (e.g., `\\server\PolicyHub`)
   - Or select a local folder for single-user testing
3. **Create Admin Account:**
   - Enter username, full name, and password
   - This will be the first administrator
4. **Start Using PolicyHub!**

## Shared Folder Structure

PolicyHub creates the following structure in your shared folder:

```
\\server\PolicyHub\
├── data\
│   └── policyhub.db          # SQLite database
├── attachments\
│   └── [document files]      # Uploaded policy documents
└── exports\
    └── [report files]        # Generated reports
```

## User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access including user management and settings |
| **Editor** | Add/edit documents, upload attachments, manage links |
| **Viewer** | Read-only access, can download and export |

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Project Structure

```
policyhub/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── app/
│   ├── application.py      # Main application class
│   ├── constants.py        # Enums and constants
│   └── theme.py            # Colors, fonts, spacing
├── core/
│   ├── config.py           # Local configuration
│   ├── database.py         # SQLite connection manager
│   ├── session.py          # User session management
│   └── permissions.py      # Role-based access control
├── models/                 # Data classes
├── services/               # Business logic
├── views/                  # UI screens
├── utils/                  # Helper functions
└── tests/                  # Pytest tests
```

## Configuration

Local configuration is stored in:
```
%LOCALAPPDATA%\PolicyHub\config.json
```

Contains:
- `shared_folder_path`: Path to the shared network folder
- `remembered_username`: Username for auto-fill (if "remember me" checked)

## Troubleshooting

### "Database is locked" error
- This can happen with slow network connections
- The app uses a 30-second timeout; wait and retry
- Ensure no other process is holding the database

### "Folder does not exist" on login
- The shared folder may have been moved or renamed
- Click "Change..." to select the new location

### Application won't start
- Check logs in `%LOCALAPPDATA%\PolicyHub\logs\policyhub.log`
- Ensure Python 3.11+ is installed
- Reinstall dependencies: `pip install -r requirements.txt`

## License

Open Source

## Version

1.0.0 - Phase 1 & 2 (Foundation + Authentication)

---

For more details, see `PolicyHub_PRD.md`.
