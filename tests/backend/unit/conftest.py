# Make sure all environment vars are loaded before the tests are executed
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent.parent / "app" / ".env"
load_dotenv(env_path)
