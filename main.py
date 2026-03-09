from pathlib import Path

from src.app import LauncherApp


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    LauncherApp(base_dir).run()
