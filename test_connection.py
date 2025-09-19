from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        client = MongoClient(os.getenv('MONGODB_URI'))
        client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Show databases
        dbs = client.list_database_names()
        print(f"📊 Databases: {dbs}")
        
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()