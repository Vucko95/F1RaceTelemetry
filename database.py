from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, UpdateOne, ASCENDING
from typing import List, Dict, Any
from loguru import logger
from config import config


class F1Database:
    def __init__(self, connection_string: str = None, database_name: str = None):
        self.connection_string = connection_string or config.MONGODB_URL
        self.database_name = database_name or config.DATABASE_NAME
        self.client = None
        self.db = None

    async def connect(self):
        """Establish database connection"""
        try:
            self.client = AsyncIOMotorClient(self.connection_string)
            self.db = self.client[self.database_name]
            await self.client.admin.command("ping")
            logger.info(f"Connected to MongoDB: {self.database_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False

    async def disconnect(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def ensure_indexes(self):
        """Create indexes for optimal query performance"""
        collections_indexes = {
            "sessions": [
                IndexModel([("session_key", ASCENDING)], unique=True),
                IndexModel([("meeting_key", ASCENDING)]),
                IndexModel([("date_start", ASCENDING)]),
            ],
            "drivers": [
                IndexModel([("session_key", ASCENDING), ("driver_number", ASCENDING)]),
                IndexModel([("driver_number", ASCENDING)]),
            ],
            "laps": [
                IndexModel(
                    [
                        ("session_key", ASCENDING),
                        ("driver_number", ASCENDING),
                        ("lap_number", ASCENDING),
                    ]
                ),
                IndexModel([("session_key", ASCENDING), ("lap_number", ASCENDING)]),
                IndexModel([("session_key", ASCENDING), ("driver_number", ASCENDING)]),
            ],
            "car_data": [
                IndexModel(
                    [
                        ("session_key", ASCENDING),
                        ("driver_number", ASCENDING),
                        ("date", ASCENDING),
                    ]
                ),
                IndexModel([("session_key", ASCENDING), ("date", ASCENDING)]),
                IndexModel([("driver_number", ASCENDING), ("date", ASCENDING)]),
            ],
            "positions": [
                IndexModel([("session_key", ASCENDING), ("date", ASCENDING)]),
                IndexModel(
                    [
                        ("session_key", ASCENDING),
                        ("driver_number", ASCENDING),
                        ("date", ASCENDING),
                    ]
                ),
            ],
            "intervals": [
                IndexModel([("session_key", ASCENDING), ("date", ASCENDING)]),
                IndexModel(
                    [
                        ("session_key", ASCENDING),
                        ("driver_number", ASCENDING),
                        ("date", ASCENDING),
                    ]
                ),
            ],
        }

        for collection_name, indexes in collections_indexes.items():
            try:
                collection = self.db[collection_name]
                await collection.create_indexes(indexes)
                logger.info(f"Created indexes for {collection_name}")
            except Exception as e:
                logger.warning(f"Error creating indexes for {collection_name}: {e}")

    async def bulk_insert(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        upsert_key: str = None,
    ):
        """Efficient bulk insertion with optional upsert"""
        if not documents:
            return 0

        try:
            collection = self.db[collection_name]

            if upsert_key:
                operations = []
                for doc in documents:
                    filter_query = {upsert_key: doc[upsert_key]}
                    operations.append(
                        UpdateOne(filter_query, {"$set": doc}, upsert=True)
                    )
                # This will write to the database
                result = await collection.bulk_write(operations, ordered=False)
                inserted_count = result.upserted_count + result.modified_count
            else:
                # Regular insert_many with duplicate handling
                try:
                    result = await collection.insert_many(documents, ordered=False)
                    inserted_count = len(result.inserted_ids)
                except Exception as bulk_error:
                    # Handle duplicate key errors silently - just count successful inserts
                    if "duplicate key error" in str(bulk_error):
                        # Extract successful inserts count from bulk write error
                        error_details = getattr(bulk_error, "details", {})
                        inserted_count = error_details.get("nInserted", 0)
                        duplicates = len(documents) - inserted_count
                        if duplicates > 0:
                            logger.debug(
                                f"Skipped {duplicates} duplicates in {collection_name}"
                            )
                    else:
                        raise bulk_error

            logger.info(
                f"Inserted/Updated {inserted_count} documents in {collection_name}"
            )
            return inserted_count

        except Exception as e:
            # Suppress the huge error message - just log the summary
            error_msg = str(e)
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "... (truncated)"
            logger.error(f"Error bulk inserting to {collection_name}: {error_msg}")
            return 0
