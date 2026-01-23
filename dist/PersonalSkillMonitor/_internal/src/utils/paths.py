import os
import sys
from pathlib import Path

class PathManager:
    """Manages application paths for both source and AppImage/binary execution."""
    
    @staticmethod
    def get_app_data_dir():
        """Returns the directory where user data should be stored."""
        # If running in AppImage or similar, use ~/.config/PSM
        if getattr(sys, 'frozen', False) or os.getenv('APPIMAGE'):
            path = Path.home() / ".config" / "PSM"
        else:
            # For development, use project root
            path = Path(__file__).parent.parent.parent
            
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_config_env_path():
        """Returns the path to config.env."""
        # config.env is bundled with the app in AppImage
        if getattr(sys, 'frozen', False) or os.getenv('APPIMAGE'):
            # When running as AppImage, the bundle root is sys._MEIPASS (for PyInstaller)
            # or it's relative to the binary. For linuxdeploy-plugin-python,
            # it's usually in the app's root within the AppImage.
            bundle_root = Path(sys.executable).parent
            if (bundle_root / "config.env").exists():
                return bundle_root / "config.env"
                
            # Fallback for some AppImage layouts
            app_dir = os.getenv('APPDIR')
            if app_dir:
                path = Path(app_dir) / "usr" / "bin" / "config.env"
                if path.exists(): return path
                path = Path(app_dir) / "config.env"
                if path.exists(): return path

        # Default to project root for dev
        return Path(__file__).parent.parent.parent / "config.env"

    @staticmethod
    def get_tokens_path():
        """Returns the path where tokens should be stored."""
        return PathManager.get_app_data_dir() / "tokens.json"

    @staticmethod
    def get_settings_path():
        """Returns the path where UI settings should be stored."""
        return PathManager.get_app_data_dir() / "ui_settings.json"

    @staticmethod
    def get_export_dir():
        """Returns the directory where exports should be saved."""
        path = PathManager.get_app_data_dir() / "exports"
        path.mkdir(parents=True, exist_ok=True)
        return path
