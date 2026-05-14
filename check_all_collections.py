#!/usr/bin/env python
"""Check all collections and documents in the database."""

from src.mongo_storage import get_client

client = get_client()
db = client["air_quality"]

print("Collections in database:")
for col_name in db.list_collection_names():
    col = db[col_name]
    count = col.count_documents({})
    print(f"  - {col_name}: {count} documents")
    
    # Sample first doc
    sample = col.find_one()
    if sample:
        print(f"    Sample fields: {list(sample.keys())}")

client.close()
