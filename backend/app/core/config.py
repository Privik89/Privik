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
        "postgresql+psycopg2://postgres:postgres@db:5432/privik",
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


