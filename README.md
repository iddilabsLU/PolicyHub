# PolicyHub

**Policy & Procedure Lifecycle Manager**

A native Windows desktop application for managing policies and procedures in regulated entities. Built with Python and CustomTkinter for a modern, professional interface.

PolicyHub provides a centralized register to track document metadata, review schedules, ownership, and relationships between policies and their implementing procedures. All data stays on your infrastructure—no cloud dependencies.

## Features

- **Document Register** — Central tracking of policies, procedures, manuals, and registers with filtering and search
- **Review Management** — Visual status indicators (overdue, due soon, on track) with configurable thresholds
- **Multi-User Access** — Role-based permissions (Admin, Editor, Viewer) via shared network folder
- **Document Linking** — Map procedures to implementing policies with bidirectional relationships
- **Attachments** — Store actual policy documents alongside metadata with version tracking
- **Audit Trail** — Complete history of all changes with timestamps and user attribution
- **Reports** — Generate PDF and Excel exports for compliance reviews
- **Dashboard** — At-a-glance statistics and items requiring attention

## Requirements

- **Operating System:** Windows 10 or 11
- **Python:** 3.11+ (for running from source)
- **Network:** Access to shared folder for multi-user deployment (optional)

## Installation

### Option 1: Run from Source

```bash
# Clone the repository
git clone https://github.com/IddiLabs/PolicyHub.git
cd PolicyHub

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Option 2: Build Standalone Executable

```bash
# Install dependencies
pip install -r requirements.txt

# Build using the build script
build.bat

# The executable will be at: build\PolicyHub.exe
```

#### Build Options

```bash
build.bat          # Standard build
build.bat test     # Run tests before building
build.bat clean    # Remove build artifacts
```

## Quick Start

1. **Launch PolicyHub** — Run `python main.py` or the built executable
2. **Database Setup** — Choose to create a new database or connect to an existing one
3. **Create Admin Account** — Set up the first administrator (new database only)
4. **Login** — Enter credentials to access the application
5. **Start Managing** — Add documents, track reviews, generate reports

### Multi-User Setup

For team collaboration via shared network folder:

**Administrator:**
1. Create new database in a shared network location (e.g., `\\server\PolicyHub`)
2. Create admin account and additional user accounts
3. Share the folder path with team members

**Team Members:**
1. Connect to existing database using the shared folder path
2. Login with credentials provided by administrator

## Project Structure

```
PolicyHub/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── build.bat               # Windows build script
├── PolicyHub.spec          # PyInstaller configuration
├── app/
│   ├── application.py      # Main application class
│   ├── constants.py        # Enums and constants
│   └── theme.py            # UI theme configuration
├── core/
│   ├── config.py           # Local configuration management
│   ├── database.py         # SQLite database manager
│   ├── session.py          # User session management
│   └── permissions.py      # Role-based access control
├── models/                 # Data classes
├── services/               # Business logic layer
├── views/                  # UI screens
├── dialogs/                # Modal dialogs
├── components/             # Reusable UI components
├── reports/                # PDF/Excel generators
├── utils/                  # Helper functions
└── tests/                  # Test suite
```

## User Roles

| Role       | Permissions                                           |
|------------|-------------------------------------------------------|
| **Admin**  | Full access including user management and settings    |
| **Editor** | Add/edit documents, upload attachments, manage links  |
| **Viewer** | Read-only access, can download attachments and export |

## Configuration

Local configuration is stored at:
```
%LOCALAPPDATA%\PolicyHub\config.json
```

Application logs are written to:
```
%LOCALAPPDATA%\PolicyHub\logs\policyhub.log
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## Utilities

### Password Reset

If you forget your admin password, use the included utility:

```bash
python reset_password.py
```

Follow the prompts to reset a user's password directly in the database.

## Tech Stack

- **UI Framework:** CustomTkinter 5.2+
- **Tables:** tksheet 7.0+
- **Database:** SQLite3
- **Password Hashing:** bcrypt
- **Reports:** ReportLab (PDF), openpyxl (Excel)
- **Packaging:** PyInstaller

## Troubleshooting

### "Database is locked" error
The application uses SQLite with WAL mode for concurrent access. With slow network connections, wait a moment and retry. Ensure no other process is holding the database.

### "Folder does not exist" on login
The shared folder may have been moved or renamed. Use the database selection dialog to reconnect.

### Application won't start
- Check logs at `%LOCALAPPDATA%\PolicyHub\logs\policyhub.log`
- Ensure Python 3.11+ is installed
- Reinstall dependencies: `pip install -r requirements.txt`

### Executable is blocked by antivirus
Some antivirus software may flag PyInstaller executables. Add an exception for `PolicyHub.exe` or run from source.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for modern UI
- Tables powered by [tksheet](https://github.com/ragardner/tksheet)
- PDF generation with [ReportLab](https://www.reportlab.com/)
- Excel support via [openpyxl](https://openpyxl.readthedocs.io/)
