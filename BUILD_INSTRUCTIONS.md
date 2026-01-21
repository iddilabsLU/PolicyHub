# PolicyHub Build Instructions

This document explains how to build PolicyHub into a standalone Windows executable and distribute it to users.

## Prerequisites

Before building, ensure you have:

1. **Python 3.11 or higher** installed and added to PATH
   - Download from: https://python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Project dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```

3. **PyInstaller** (installed automatically by build script if missing)

## Building the Executable

### Quick Build

Run the build script from the project root:

```bash
build.bat
```

The executable will be created at: `build\PolicyHub.exe`

### Build with Tests

To run tests before building:

```bash
build.bat test
```

### Clean Build Artifacts

To remove all build files:

```bash
build.bat clean
```

## Output

After a successful build:

- **Location:** `build\PolicyHub.exe`
- **Size:** Approximately 80-150 MB
- **Type:** Single-file Windows executable

## Distribution

### Single-User Setup

For users who will work independently with their own database:

1. Copy `build\PolicyHub.exe` to the target machine
2. Run `PolicyHub.exe`
3. On first launch, the Database Selection dialog appears
4. Click **"Create New Database"**
5. Choose a folder for the database file (e.g., `Documents\PolicyHub`)
6. Create the admin account when prompted
7. Login and start using the application

### Multi-User / Shared Database Setup

For teams sharing a single database on a network drive:

**Administrator (First Setup):**
1. Copy `PolicyHub.exe` to a shared network location or distribute to users
2. Run `PolicyHub.exe`
3. Click **"Create New Database"**
4. Choose a **shared network folder** all users can access (e.g., `\\server\shared\PolicyHub`)
5. Create the admin account
6. Share the database folder path with team members

**Team Members:**
1. Run `PolicyHub.exe`
2. Click **"Connect to Existing Database"**
3. Navigate to the shared network folder containing `policyhub.db`
4. Select the database file
5. Login with credentials provided by the administrator

## First-Time User Experience

When PolicyHub runs for the first time on a machine:

1. **Database Selection Dialog** - Choose to create new or connect to existing database
2. **Admin Creation** (new database only) - Set up the first administrator account
3. **Login Screen** - Enter credentials to access the application
4. **Main Dashboard** - Start managing policies and procedures

## Troubleshooting

### "Python not found" Error

- Ensure Python 3.11+ is installed
- Verify Python is in your PATH: run `python --version` in command prompt
- Reinstall Python with "Add Python to PATH" checked

### "Module not found" Errors During Build

Install missing dependencies:
```bash
pip install -r requirements.txt
```

### Executable Won't Start

- Check Windows Defender or antivirus isn't blocking the file
- Right-click the exe and select "Run as administrator" if needed
- Ensure Visual C++ Redistributable is installed (required for some Python packages)

### "Database is locked" Error

This occurs when multiple users access the same database simultaneously:
- The application uses SQLite with WAL mode for better concurrency
- Wait a moment and retry the operation
- Ensure all users are on the same network with stable connections

### Build Takes Too Long

First builds download and cache dependencies. Subsequent builds are faster.
Typical build time: 2-5 minutes depending on system performance.

### Executable is Too Large

The executable includes all dependencies (~80-150 MB is normal).
PyInstaller bundles the Python interpreter and all required libraries.

## Advanced: Manual Build

If you prefer running PyInstaller directly:

```bash
pyinstaller PolicyHub.spec --noconfirm --distpath build
```

## Build Configuration

The build is configured in `PolicyHub.spec`:

- **Hidden imports:** customtkinter, tksheet, bcrypt, reportlab, openpyxl
- **Excluded packages:** numpy, pandas, matplotlib (not needed, reduces size)
- **Console:** Disabled (GUI-only application)
- **Single file:** Yes (all dependencies bundled)

## Requirements Reference

Key dependencies for building:

| Package | Purpose |
|---------|---------|
| customtkinter | Modern UI framework |
| tksheet | Data tables |
| bcrypt | Password hashing |
| reportlab | PDF generation |
| openpyxl | Excel generation |
| pyinstaller | Executable packaging |

## Support

For issues or questions:
- Check the troubleshooting section above
- Review `CLAUDE.md` for development documentation
- Check application logs in `%LOCALAPPDATA%\PolicyHub\logs`
