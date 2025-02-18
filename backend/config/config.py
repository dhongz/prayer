import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    HUGGINGFACE_API_KEY = os.getenv("HUGGGINGFACE_API_KEY")


config = Config()