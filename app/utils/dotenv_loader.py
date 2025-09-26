from pathlib import Path

from dotenv import load_dotenv


def load_env():
    # Load .env file if exists
    dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path)
