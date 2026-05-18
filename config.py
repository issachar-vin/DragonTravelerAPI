from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "dragon_travelers_guide"
    images_dir: str = "images"
    secret_key: str = "dev-secret-key-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_days: int = 7
    # Comma-separated list of allowed CORS origins
    allowed_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
