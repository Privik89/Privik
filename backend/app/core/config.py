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
    enable_hmac_auth: bool = os.getenv("ENABLE_HMAC_AUTH", "true").lower() == "true"
    enable_jwt_auth: bool = os.getenv("ENABLE_JWT_AUTH", "false").lower() == "true"
    
    # AI/ML Services
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    virustotal_api_key: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    # CAPE Sandbox
    cape_enabled: bool = os.getenv("CAPE_ENABLED", "false").lower() == "true"
    cape_base_url: str = os.getenv("CAPE_BASE_URL", "http://localhost:8001")
    cape_api_token: str = os.getenv("CAPE_API_TOKEN", "")
    
    # Email Integration
    gmail_client_id: str = os.getenv("GMAIL_CLIENT_ID", "")
    gmail_client_secret: str = os.getenv("GMAIL_CLIENT_SECRET", "")
    gmail_refresh_token: str = os.getenv("GMAIL_REFRESH_TOKEN", "")
    o365_client_id: str = os.getenv("O365_CLIENT_ID", "")
    o365_client_secret: str = os.getenv("O365_CLIENT_SECRET", "")
    o365_tenant_id: str = os.getenv("O365_TENANT_ID", "")
    enable_gmail_ingest: bool = os.getenv("ENABLE_GMAIL_INGEST", "false").lower() == "true"
    enable_o365_ingest: bool = os.getenv("ENABLE_O365_INGEST", "false").lower() == "true"
    enable_imap_ingest: bool = os.getenv("ENABLE_IMAP_INGEST", "false").lower() == "true"
    
    # Security Settings
    sandbox_timeout: int = int(os.getenv("SANDBOX_TIMEOUT", "30"))
    max_file_size: str = os.getenv("MAX_FILE_SIZE", "50MB")
    allowed_file_types: str = os.getenv("ALLOWED_FILE_TYPES", ".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar,.7z")
    # HMAC Auth
    hmac_api_key_id: str = os.getenv("HMAC_API_KEY_ID", "privik-agent")
    hmac_api_secret: str = os.getenv("HMAC_API_SECRET", "change-me")
    hmac_auth_ttl_seconds: int = int(os.getenv("HMAC_TTL_SECONDS", "300"))
    # JWT Auth
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me")
    jwt_admin_role: str = os.getenv("JWT_ADMIN_ROLE", "admin")
    
    # Proxy Settings
    proxy_base_url: str = os.getenv("PROXY_BASE_URL", "https://proxy.privik.local")
    sandbox_base_url: str = os.getenv("SANDBOX_BASE_URL", "https://sandbox.privik.local")
    # UI proxy guard
    ui_ip_allowlist: str = os.getenv("UI_IP_ALLOWLIST", "")
    ui_required_roles: str = os.getenv("UI_REQUIRED_ROLES", "")
    
    # Performance & Reliability Configuration
    # Redis Configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Database Optimization
    db_pool_size: int = int(os.getenv("DB_POOL_SIZE", "20"))
    db_max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    db_pool_recycle: int = int(os.getenv("DB_POOL_RECYCLE", "3600"))
    db_pool_timeout: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    
    # Logging Configuration
    log_directory: str = os.getenv("LOG_DIRECTORY", "logs")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")
    
    # Health Monitoring
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    health_check_timeout: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "10"))
    
    # Performance Monitoring
    enable_performance_monitoring: bool = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
    metrics_retention_days: int = int(os.getenv("METRICS_RETENTION_DAYS", "30"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


