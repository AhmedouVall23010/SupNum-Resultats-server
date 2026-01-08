from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.core.config import settings

# Create MongoDB client
client = MongoClient(settings.MONGODB_URL)

# Get database
db = client[settings.DATABASE_NAME]

# Test connection
def test_connection():
    try:
        client.admin.command('ping')
        print("MongoDB connection successful!")
        return True
    except ConnectionFailure:
        print("MongoDB connection failed!")
        return False

# Get users collection
users_collection = db.users

# Get refresh tokens collection
refresh_tokens_collection = db.refresh_tokens

# Get notes collection
notes_collection = db.notes
# Note: _id is automatically unique in MongoDB, and we use matricule as _id

