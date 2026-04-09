import os


class Settings:
    PROJECT_NAME: str = "Hackathon Management API"
    API_PREFIX: str = "/api"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:1234@localhost:5432/hackathon_lab1",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "very-secret-key-for-lab")



settings = Settings()
