import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
    JWT_SECRET = os.getenv("JWT_SECRET")
    WEAVIATE_URL = os.getenv("WEAVIATE_URL")
    APPLE_TEAM_ID = os.getenv("APPLE_TEAM_ID")
    APPLE_KEY_ID = os.getenv("APPLE_KEY_ID")
    APPLE_BUNDLE_ID = os.getenv("APPLE_BUNDLE_ID")
    APPLE_PRIVATE_KEY = os.getenv("APPLE_PRIVATE_KEY")
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

config = Config()