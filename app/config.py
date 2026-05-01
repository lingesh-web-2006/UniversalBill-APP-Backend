"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration loaded from environment."""
    SECRET_KEY        = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://postgres:Postgre@localhost:5432/voiceinvoice")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 300}

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    CORS_ORIGINS      = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    JWT_EXPIRY_HOURS  = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

    # AI model to use for invoice parsing (Groq)
    AI_MODEL = "llama-3.3-70b-versatile"
    AI_MAX_TOKENS = 2048


class DevelopmentConfig(Config):
    DEBUG = True
    FLASK_ENV = "development"


class ProductionConfig(Config):
    DEBUG = False
    FLASK_ENV = "production"
