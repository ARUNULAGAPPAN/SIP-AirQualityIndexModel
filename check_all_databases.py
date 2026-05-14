#!/usr/bin/env python
"""Check what databases and data exist on the cloud MongoDB cluster."""

from pymongo import MongoClient
import os

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://arun:arun%40123@cluster0.dher6tt.mongodb.net/?appName=Cluster0")

client = MongoClient(MONGODB_URL, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)

try:
    # List all databases
    db_list = client.list_database_names()
    print(f"Databases on cluster: {db_list}\n")
    
    # Check each database for collections
    for db_name in db_list:
        if db_name not in ['admin', 'config', 'local']:  # Skip system databases
            db = client[db_name]
            collections = db.list_collection_names()
            print(f"\nDatabase '{db_name}':")
            
            for col_name in collections:
                col = db[col_name]
                count = col.count_documents({})
                print(f"  - {col_name}: {count} documents")
                
                # Show sample if there's data
                if count > 0:
                    sample = col.find_one()
                    if 'latitude' in sample or 'lon' in sample or 'coordinates' in sample:
                        if 'latitude' in sample:
                            print(f"    Example location: ({sample.get('latitude')}, {sample.get('longitude')})")
                        
finally:
    client.close()
