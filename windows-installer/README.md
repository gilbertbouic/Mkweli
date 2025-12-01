# Mkweli AML - Windows Installer

This directory contains files for building a one-click Windows installer for Mkweli AML.

## Files

| File | Purpose |
|------|---------|
| `setup.iss` | Inno Setup script for building the installer |
| `setup-config.bat` | Helper script for Docker checks and app management |
| `MkweliLauncher.vbs` | VBScript GUI launcher (no terminal window) |

## Building the Installer

### Prerequisites

1. Install [Inno Setup 6.x](https://jrsoftware.org/isdl.php) (free)
2. Have all application files ready in the parent directory

### Build Steps

1. Open Inno Setup Compiler
2. Open `setup.iss` from this folder
3. Click **Build → Compile** (or press F9)
4. The installer will be created in the `output/` folder

### Optional: Custom Images

To customize the installer appearance:

1. Create `wizard-image.bmp` (164 × 314 pixels)
2. Create `wizard-small-image.bmp` (55 × 55 pixels)
3. Place them in this folder before building

## User Experience

### What the Installer Does

1. **System Check** - Verifies Windows version and RAM
2. **Docker Check** - Checks if Docker Desktop is installed
3. **File Installation** - Copies application files to Program Files
4. **Shortcuts** - Creates desktop and Start Menu shortcuts
5. **Launch Option** - Offers to start the app immediately

### What the Launcher Does

The `MkweliLauncher.vbs` provides a user-friendly menu:

- Start/Stop/Restart the application
- Open the dashboard in a browser
- View application logs
- Check system status

**Key feature:** No terminal window is shown to the user.

## Customization

### Changing the App Version

Edit `setup.iss` and update:
```pascal
#define MyAppVersion "1.0.0"
```

### Changing System Requirements

Edit `setup.iss` and update the constants:
```pascal
const
  MIN_RAM_MB = 4096;
  MIN_DISK_GB = 5;
```

### Changing the Port

Edit `MkweliLauncher.vbs` and `setup-config.bat`:
```vbscript
Const APP_URL = "http://localhost:8000"
```
```batch
set APP_URL=http://localhost:8000
```

## Testing

### Test the Installer

1. Build the installer on a development machine
2. Copy to a clean Windows VM or test machine
3. Run the installer and verify:
   - System requirements check works
   - Docker check works
   - Files are installed correctly
   - Shortcuts are created
   - Application launches successfully

### Test the Launcher

1. Run `MkweliLauncher.vbs` directly
2. Test each menu option
3. Verify no terminal windows appear

## Troubleshooting

### "Inno Setup cannot find file"

Make sure the relative paths in `setup.iss` are correct:
- `Source: "..\*"` should point to the main app folder
- Icon and license files must exist

### "VBScript error"

Run `cscript MkweliLauncher.vbs` from command prompt to see detailed errors.

### "Docker not detected"

The scripts check for `docker` in PATH. Ensure Docker Desktop is properly installed and added to system PATH.

## Support

- **Email:** gilbert@mkweli.tech
- **Issues:** https://github.com/gilbertbouic/Mkweli/issues
