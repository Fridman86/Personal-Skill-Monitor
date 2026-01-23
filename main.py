from src.utils.config import Config
from src.gui.app import EVEApp

def main():
    config = Config()
    
    # Ensure mandatory config is present
    if not config.data["client_id"]:
        print("[ERROR] EVE_CLIENT_ID is missing in config.env")
        return

    app = EVEApp(config)
    app.mainloop()

if __name__ == "__main__":
    main()
