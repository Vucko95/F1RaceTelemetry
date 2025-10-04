import os


class Config:
    MONGODB_URL: str = os.getenv(
        "MONGODB_URL",
        "mongodb://admin:Supersecret1@localhost:27017/openf1?authSource=admin",
    )
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "openf1")
    OPENF1_BASE_URL: str = "https://api.openf1.org/v1"
    BATCH_SIZE: int = 5000
    MAX_CONCURRENT_REQUESTS: int = 5


config = Config()
