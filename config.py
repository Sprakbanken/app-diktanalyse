import os


class Config:
    """Application configuration"""

    # Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"

    # Threading settings
    MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "4"))
