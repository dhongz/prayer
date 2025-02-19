import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")


config = Config()