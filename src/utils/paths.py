import os
import sys
from pathlib import Path

class PathManager:
    """Manages application paths for both source and AppImage/binary execution."""
    
    @staticmethod
    def get_app_data_dir():
        """Returns the directory where user data should be stored."""
        if sys.platform == "win32":
            # Windows: %APPDATA%/PSM
            appdata = os.environ.get("APPDATA")
            if appdata:
                path = Path(appdata) / "PSM"
            else:
                path = Path.home() / "AppData" / "Roaming" / "PSM"
        else:
            # Linux/Others: ~/.config/PSM
            path = Path.home() / ".config" / "PSM"
            
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

    @staticmethod
    def get_cache_dir():
        """Returns the directory where cached ESI data should be stored."""
        path = PathManager.get_app_data_dir() / "cache"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_icon_path():
        """Returns the path to the application icon."""
        # Check bundled first (AppImage/PyInstaller)
        if getattr(sys, 'frozen', False) or os.getenv('APPIMAGE'):
            # PyInstaller puts data in sys._MEIPASS
            if hasattr(sys, '_MEIPASS'):
                path = Path(sys._MEIPASS) / "icon.png"
                if path.exists(): return path
            
            # Fallback for linuxdeploy layout
            bundle_root = Path(sys.executable).parent
            if (bundle_root / "icon.png").exists():
                return bundle_root / "icon.png"
            
            app_dir = os.getenv('APPDIR')
            if app_dir:
                path = Path(app_dir) / "icon.png"
                if path.exists(): return path
        
        # Default to source location for dev
        return Path(__file__).parent.parent / "gui" / "assets" / "icon.png"
