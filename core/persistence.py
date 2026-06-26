import json
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.join("outputs", "talent_db.json")

def save_talent_data(data: list):
    """Saves the processed data list to a local JSON file."""
    try:
        os.makedirs("outputs", exist_ok=True)
        with open(DB_PATH, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Persistence: Saved {len(data)} records to {DB_PATH}")
    except Exception as e:
        logger.error(f"Persistence Save Error: {e}")

def load_talent_data() -> list:
    """Loads the processed data from the local JSON file."""
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, "r") as f:
            data = json.load(f)
        logger.info(f"Persistence: Loaded {len(data)} records from {DB_PATH}")
        return data
    except Exception as e:
        logger.error(f"Persistence Load Error: {e}")
        return []
