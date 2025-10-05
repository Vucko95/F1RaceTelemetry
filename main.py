import asyncio
import sys
from loguru import logger
from data_ingestion import TestDataIngestion
from models import Session


logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
)


async def run_test_ingestion():
    """Main function to run test data ingestion"""
    logger.info("Starting test data ingestion...")

    async with TestDataIngestion() as ingestion:
        try:
            # Get latest race session
            latest_session = await ingestion.fetch_latest_session()
            session_key = latest_session["session_key"]

            # Store session metadata from JSON to PYDantic model and insert into DB
            session = Session(**latest_session)
            await ingestion.db.bulk_insert(
                "sessions", [session.model_dump()], upsert_key="session_key"
            )

            # Ingest all data for this session
            await ingestion.ingest_session_data(session_key)

            logger.success("Test data ingestion completed successfully!")

        except Exception as e:
            logger.error(f"Test ingestion failed: {e}")
            raise


def main():
    """Main entry point"""
    logger.info("F1 Data Ingestion Test")
    logger.info("=" * 50)

    try:
        asyncio.run(run_test_ingestion())
        logger.success("Test completed successfully!")

    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
