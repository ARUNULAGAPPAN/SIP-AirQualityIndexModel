#!/usr/bin/env python
"""Check MongoDB status and migrate data if needed."""

from src.mongo_storage import get_client, DB_NAME
from pymongo import MongoClient

# Check current MongoDB connection
print("Checking current MongoDB connection...")
client = get_client()

try:
    # Ping to verify connection
    client.admin.command('ping')
    print("✓ Connected to MongoDB successfully")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    exit(1)

# Check database
db = client[DB_NAME]
collections = db.list_collection_names()
print(f"\nCollections in '{DB_NAME}' database: {collections if collections else 'None (empty)'}")

# Check sensors_readings collection
sensor_col = db["sensor_readings"]
count = sensor_col.count_documents({})
print(f"Documents in sensor_readings collection: {count}")

client.close()

if count == 0:
    print(f"\n⚠️  The {DB_NAME} database is empty!")
    print("The data needs to be migrated or populated.")
    print("\nOptions:")
    print("1. Have hardware send data to POST /ingest endpoint")
    print("2. Or provide the MongoDB URI where the existing data is stored")
