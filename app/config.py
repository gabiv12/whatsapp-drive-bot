import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PORT = int(os.getenv("PORT", 8000))
    APP_ENV = os.getenv("APP_ENV", "development")

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER = os.getenv(
        "TWILIO_WHATSAPP_NUMBER",
        os.getenv("TWILIO_PHONE_NUMBER", ""),
    )

    GOOGLE_CLIENT_EMAIL = os.getenv("GOOGLE_CLIENT_EMAIL", "")
    GOOGLE_PRIVATE_KEY = os.getenv("GOOGLE_PRIVATE_KEY", "")
    GOOGLE_DRIVE_ROOT_FOLDER_ID = os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID", "")

    ALLOWED_OWNER_NUMBERS = os.getenv("ALLOWED_OWNER_NUMBERS", "")

    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
    TMP_DIR = os.path.join(os.path.dirname(__file__), "..", "tmp", "uploads")
    CONVERSATIONS_FILE = os.path.join(DATA_DIR, "conversations.json")
    PENDING_FILE = os.path.join(DATA_DIR, "pending_uploads.json")
    FOLDERS_FILE = os.path.join(DATA_DIR, "folders.json")
