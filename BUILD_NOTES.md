# Build Notes - Personal Skill Monitor AppImage

## Features
- **Self-contained**: Bundles Python 3.12 and all required libraries.
- **Persistent Data**: Stores tokens and settings in `~/.config/PSM/`.
- **Desktop Integrated**: Includes application icon and desktop entry.

## Execution
To run the application:
1. Download `PersonalSkillMonitor-x86_64.AppImage`.
2. Mark it as executable:
   ```bash
   chmod +x PersonalSkillMonitor-x86_64.AppImage
   ```
3. Run it from the terminal or double-click in your file manager:
   ```bash
   ./PersonalSkillMonitor-x86_64.AppImage
   ```

## Runtime Paths
- **Config & Tokens**: `~/.config/PSM/tokens.json`
- **UI Settings**: `~/.config/PSM/ui_settings.json`
- **Exports**: `~/.config/PSM/exports/` (Default location, can be changed in the export dialog)

## Known Issues
- Requires a desktop environment with FUSE support (standard for Linux Mint/Ubuntu).
- If it fails to run, ensure `libfuse2` is installed on your system.

## Build Process (for developers)
Run the automated build script:
```bash
./build_appimage.sh
```
This script will:
1. Create a clean virtual environment.
2. Install build dependencies (PyInstaller, etc.).
3. Bundle the app using PyInstaller.
4. Package everything into an AppImage using `linuxdeploy`.
