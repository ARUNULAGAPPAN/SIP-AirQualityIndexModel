#!/usr/bin/env python
"""Migrate MongoDB indexes from lat/lon to GeoJSON format."""
import os
from pymongo import MongoClient

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "air_quality"

def migrate_indexes():
    """Drop old indexes and create new GeoJSON indexes."""
    try:
        client = MongoClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=20000,
            tlsAllowInvalidCertificates=True,
        )
        db = client[DB_NAME]
        
        print("=" * 70)
        print("MONGODB INDEX MIGRATION")
        print("=" * 70)
        
        # Migrate sensor_readings collection
        print("\n[1/2] Migrating sensor_readings indexes...")
        sensor_col = db["sensor_readings"]
        
        # Drop old indexes
        try:
            sensor_col.drop_index("latitude_2dsphere_longitude_2dsphere")
            print("  ✓ Dropped old latitude/longitude index")
        except Exception:
            pass
        
        # Create new indexes
        sensor_col.drop_index("timestamp_1") if sensor_col.index_information().get("timestamp_1") else None
        sensor_col.create_index("timestamp")
        sensor_col.create_index([("location", "2dsphere")])
        print("  ✓ Created new geo-spatial index on location field")
        
        # Migrate predictions collection
        print("\n[2/2] Migrating predictions indexes...")
        pred_col = db["predictions"]
        
        # Drop old indexes
        try:
            pred_col.drop_index("latitude_2dsphere_longitude_2dsphere")
            print("  ✓ Dropped old latitude/longitude index")
        except Exception:
            pass
        
        # Create new indexes
        pred_col.drop_index("timestamp_1") if pred_col.index_information().get("timestamp_1") else None
        pred_col.create_index("timestamp")
        pred_col.create_index([("location", "2dsphere")])
        pred_col.create_index("sensor_reading_id")
        print("  ✓ Created new geo-spatial index on location field")
        
        print("\n" + "=" * 70)
        print("✓ INDEX MIGRATION COMPLETE")
        print("=" * 70)
        
        # Show final indexes
        print("\nFinal indexes:")
        print("  sensor_readings:", list(sensor_col.index_information().keys()))
        print("  predictions:", list(pred_col.index_information().keys()))
        
        client.close()
    except Exception as e:
        print(f"Error migrating indexes: {e}")
        raise

if __name__ == "__main__":
    migrate_indexes()
