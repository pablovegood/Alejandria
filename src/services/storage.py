import json
import os
from datetime import datetime

DATA_FILE = "data.json"

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "books": [], "reservations": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": [], "books": [], "reservations": []}

