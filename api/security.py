import os
from dotenv import load_dotenv, find_dotenv
from fastapi.security.api_key import APIKeyQuery

load_dotenv(find_dotenv())

API_KEY = os.environ["API_KEY"]
API_KEY_NAME = "api_key"
API_KEY_QUERY = APIKeyQuery(name=API_KEY_NAME, auto_error=True)
