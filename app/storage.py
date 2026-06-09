import json
import os

from app.config import Config


def ensure_data_dirs():
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    os.makedirs(Config.TMP_DIR, exist_ok=True)


def read_json(file_path, default_factory=dict):
    ensure_data_dirs()
    try:
        if not os.path.exists(file_path):
            return default_factory()
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            return json.loads(content) if content else default_factory()
    except (json.JSONDecodeError, OSError):
        return default_factory()


def write_json(file_path, data):
    ensure_data_dirs()
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
        file.write("\n")


def get_conversation(user_id):
    conversations = read_json(Config.CONVERSATIONS_FILE)
    return conversations.get(user_id, {"state": "waiting_files"})


def save_conversation(user_id, data):
    conversations = read_json(Config.CONVERSATIONS_FILE)
    conversations[user_id] = data
    write_json(Config.CONVERSATIONS_FILE, conversations)
