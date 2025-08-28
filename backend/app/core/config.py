import os
from functools import lru_cache


class Settings:
    """Central application configuration loaded from environment variables.

    This class is intentionally verbose to make it clear what each setting does.
    """

    # App
    app_name: str = os.getenv("APP_NAME", "Privik Email Security API")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./privik.db",  # Force SQLite for development
    )

    # CORS / API
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    # Object storage (S3-compatible like MinIO)
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "minioadmin")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "minioadmin")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "privik-artifacts")

    # Redis (for jobs/queues in future)
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Feature flags
    enable_clamav: bool = os.getenv("ENABLE_CLAMAV", "false").lower() == "true"
    enable_fake_sandbox: bool = os.getenv("ENABLE_FAKE_SANDBOX", "true").lower() == "true"
    
    # AI/ML Services
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    virustotal_api_key: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    
    # Email Integration
    gmail_client_id: str = os.getenv("GMAIL_CLIENT_ID", "")
    gmail_client_secret: str = os.getenv("GMAIL_CLIENT_SECRET", "")
    o365_client_id: str = os.getenv("O365_CLIENT_ID", "")
    o365_client_secret: str = os.getenv("O365_CLIENT_SECRET", "")
    
    # Security Settings
    sandbox_timeout: int = int(os.getenv("SANDBOX_TIMEOUT", "30"))
    max_file_size: str = os.getenv("MAX_FILE_SIZE", "50MB")
    allowed_file_types: str = os.getenv("ALLOWED_FILE_TYPES", ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar,.7z")
    
    # Proxy Settings
    proxy_base_url: str = os.getenv("PROXY_BASE_URL", "https://proxy.privik.local")
    sandbox_base_url: str = os.getenv("SANDBOX_BASE_URL", "https://sandbox.privik.local")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


