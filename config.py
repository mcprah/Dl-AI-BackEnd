from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    MONGODB_URI = os.getenv('MONGODB_URI')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG')
