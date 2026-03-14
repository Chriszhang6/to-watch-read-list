"""
配置管理模块 - 统一管理环境变量和应用配置
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """应用配置类"""

    # ========== 环境 ==========
    ENV = os.getenv("ENV", "development")
    DEBUG = ENV == "development"
    USE_MOCK_EXTERNAL = os.getenv("USE_MOCK_EXTERNAL", "false").lower() == "true"

    # ========== 认证 ==========
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError("❌ SECRET_KEY environment variable is required")

    SESSION_COOKIE_NAME = "session"
    SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

    # ========== 数据库 ==========
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    # Handle Heroku PostgreSQL URL format
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # ========== 外部 API ==========
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

    # ========== 邮件发送 ==========
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")

    # ========== CORS ==========
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:8000,http://localhost:3000"
    ).split(",")

    # ========== 应用信息 ==========
    APP_TITLE = "Watchlist"
    APP_VERSION = "2.0.0"

    @classmethod
    def print_config(cls) -> None:
        """打印当前配置（用于调试）"""
        print("\n" + "=" * 60)
        print("📋 Application Configuration")
        print("=" * 60)
        print(f"Environment: {cls.ENV}")
        print(f"Debug Mode: {cls.DEBUG}")
        print(f"Use Mock External APIs: {cls.USE_MOCK_EXTERNAL}")
        print(f"Database: {cls.DATABASE_URL[:50]}...")
        print(f"YouTube API Key: {'✅ Configured' if cls.YOUTUBE_API_KEY else '❌ Not configured'}")
        print(f"SendGrid API Key: {'✅ Configured' if cls.SENDGRID_API_KEY else '❌ Not configured'}")
        print(f"Allowed Origins: {', '.join(cls.ALLOWED_ORIGINS)}")
        print("=" * 60 + "\n")


settings = Settings()
