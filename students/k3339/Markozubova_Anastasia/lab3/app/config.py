import os


class Settings:
    PROJECT_NAME: str = "Hackathon Parser Lab 3"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:1234@localhost:5432/hackathon_lab3",
    )
    PARSER_SERVICE_URL: str = os.getenv("PARSER_SERVICE_URL", "http://localhost:8001")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")


settings = Settings()
