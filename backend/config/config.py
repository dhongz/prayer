import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


config = Config()