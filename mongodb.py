import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

load_dotenv()

uri = os.environ.get('MONGODB_URI')
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.get_database('accounts_db')
users_collection = db.get_collection('accounts')
