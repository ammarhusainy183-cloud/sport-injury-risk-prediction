import os
from datetime import timedelta


class Config:
    """Base configuration"""

    # Database
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        # Render/PostgreSQL sometimes provides postgres://
        # SQLAlchemy expects postgresql://
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://",
                "postgresql://",
                1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Local development uses SQLite
        SQLALCHEMY_DATABASE_URI = "sqlite:///sport_injury.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security
    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or "dev-secret-key-change-in-production"
    )

    JWT_SECRET_KEY = (
        os.environ.get("JWT_SECRET_KEY")
        or "jwt-secret-key-change-in-production"
    )

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration"""

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    TESTING = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}