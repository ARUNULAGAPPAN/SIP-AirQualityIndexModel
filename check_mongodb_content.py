#!/usr/bin/env python
"""Check what's in the new MongoDB."""

from src.mongo_storage import get_client

client = get_client()
db = client["airquality"]

print("Collections in airquality database:")
for col_name in db.list_collection_names():
    col = db[col_name]
    count = col.count_documents({})
    print(f"  - {col_name}: {count} documents")
    
    if count > 0:
        sample = col.find_one()
        print(f"    Fields: {list(sample.keys())[:10]}")

# Also check if there's data in other databases
print("\n\nAll databases on this connection:")
admin = client.admin
databases = admin.list_database_names()
for db_name in sorted(databases):
    print(f"  - {db_name}")

client.close()
