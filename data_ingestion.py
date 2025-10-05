import asyncio
import aiohttp
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime

from database import F1Database
from models import Session, Driver, Lap, CarData, Position, Interval
from config import config

class TestDataIngestion:
    def __init__(self):
        self.db = F1Database()
        self.session = None
        
    async def __aenter__(self):
        await self.db.connect()
        await self.db.ensure_indexes()
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        await self.db.disconnect()
    
    async def fetch_latest_session(self) -> Dict[str, Any]:
        """Fetch the latest race session"""
        url = f"{config.OPENF1_BASE_URL}/sessions?session_type=Race&year=2024"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                sessions = await response.json()
                if sessions:
                    # Get the most recent race
                    latest_session = max(sessions, key=lambda x: x['date_start'])
                    logger.info(f"Found latest race: {latest_session['session_name']} - {latest_session['location']}")
                    return latest_session
        
        raise Exception("Could not fetch latest session")
    
    async def ingest_session_data(self, session_key: int):
        """Ingest all data for a specific session"""
        logger.info(f"Starting data ingestion for session {session_key}")
        
        # Ingest different data types sequentially to see progress
        logger.info("Ingesting drivers...")
        drivers_count = await self.ingest_drivers(session_key)
        
        logger.info("Ingesting laps...")
        laps_count = await self.ingest_laps(session_key)

        logger.info("Ingesting positions...")
        positions_count = await self.ingest_positions(session_key)
        
        # logger.info("Ingesting intervals...")
        # intervals_count = await self.ingest_intervals(session_key)

        # logger.info("Ingesting car data...")
        # car_data_count = await self.ingest_car_data(session_key)
        
        # Print final statistics
        logger.info("\n" + "="*50)
        logger.info("INGESTION SUMMARY")
        logger.info("="*50)
        logger.info(f"Drivers: {drivers_count}")
        logger.info(f"Laps: {laps_count}")
        logger.info(f"Positions: {positions_count}")
        # logger.info(f"Intervals: {intervals_count}")
        # logger.info(f"Car Data: {car_data_count}")

        stats = await self.db.get_collection_stats()
        logger.info("\nDATABASE STATISTICS:")
        for collection, count in stats.items():
            logger.info(f"  {collection}: {count:,} documents")

    async def ingest_drivers(self, session_key: int):
        """Ingest driver data"""
        url = f"{config.OPENF1_BASE_URL}/drivers?session_key={session_key}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f"  Fetched {len(data)} drivers from API")
                
                drivers = []
                for item in data:
                    try:
                        driver = Driver(**item)
                        drivers.append(driver.model_dump())
                    except Exception as e:
                        logger.warning(f"Error processing driver {item.get('driver_number', 'unknown')}: {e}")
                
                count = await self.db.bulk_insert("drivers", drivers)
                logger.info(f" Stored {count} drivers in database")
                return count

        logger.error(" Failed to fetch drivers data")
        return 0
    
    async def ingest_laps(self, session_key: int):
        """Ingest lap data"""
        url = f"{config.OPENF1_BASE_URL}/laps?session_key={session_key}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                laps = []
                for item in data:
                    try:
                        # Convert date string to datetime if needed
                        if isinstance(item.get('date_start'), str):
                            item['date_start'] = datetime.fromisoformat(item['date_start'].replace('Z', '+00:00'))
                        
                        lap = Lap(**item)
                        laps.append(lap.model_dump())
                        
                        if len(laps) >= config.BATCH_SIZE:
                            await self.db.bulk_insert("laps", laps)
                            laps = []
                            logger.debug(f"  Processed batch of {config.BATCH_SIZE} laps")
                            
                    except Exception as e:
                        # Only show first 3 errors to avoid spam
                        if len(laps) < 3:
                            logger.warning(f"Error processing lap data for driver {item.get('driver_number', 'unknown')}: {str(e)[:100]}...")
                        elif len(laps) == 3:
                            logger.warning("More lap validation errors found... (suppressing further messages)")
                
                # Insert remaining laps
                if laps:
                    await self.db.bulk_insert("laps", laps)
                
                # Insert remaining laps
                if laps:
                    await self.db.bulk_insert("laps", laps)
                
                total_count = len(data)
                successful_count = len([item for item in data if self._validate_lap_item(item)])
                logger.info(f"   Processed {successful_count}/{total_count} laps successfully")
                return successful_count
        
        logger.error("Failed to fetch laps data")
        return 0
    
    async def ingest_positions(self, session_key: int):
        """Ingest position data"""
        url = f"{config.OPENF1_BASE_URL}/position?session_key={session_key}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                positions = []
                for item in data:
                    try:
                        if isinstance(item.get('date'), str):
                            item['date'] = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
                        
                        position = Position(**item)
                        positions.append(position.model_dump())
                        
                        if len(positions) >= config.BATCH_SIZE:
                            await self.db.bulk_insert("positions", positions)
                            positions = []
                            logger.debug(f" Processed batch of {config.BATCH_SIZE} positions")
                            
                    except Exception as e:
                        logger.warning(f"Error processing position data: {e}")
                
                if positions:
                    await self.db.bulk_insert("positions", positions)
                
                total_count = len(data)
                logger.info(f"Ingested {total_count} position records")
                return total_count
        
        logger.error("Failed to fetch position data")
        return 0
    
    async def ingest_intervals(self, session_key: int):
        """Ingest interval data"""
        url = f"{config.OPENF1_BASE_URL}/intervals?session_key={session_key}"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                logger.info(f" Fetched {len(data)} intervals from API")
                
                intervals = []
                progress_count = 0 
                for item in data:
                    try:
                        if isinstance(item.get('date'), str):
                            item['date'] = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
                        
                        interval = Interval(**item)
                        intervals.append(interval.model_dump())
                        
                        if len(intervals) >= config.BATCH_SIZE:
                            await self.db.bulk_insert("intervals", intervals)
                            intervals = []
                            progress_count += config.BATCH_SIZE
                            if progress_count % (config.BATCH_SIZE * 5) == 0:  # Show progress every 5k records
                                logger.info(f" Progress: {progress_count:,}/{len(data):,} intervals processed")
                            
                    except Exception as e:
                        # Only show first 3 errors to avoid spam
                        if len(intervals) < 3:
                            gap_value = item.get('gap_to_leader', 'unknown')
                            interval_value = item.get('interval', 'unknown')
                            logger.warning(f"Error processing interval data for driver {item.get('driver_number', 'unknown')}: gap='{gap_value}', interval='{interval_value}'")
                        elif len(intervals) == 3:
                            logger.warning("More interval validation errors found... (suppressing further messages)")
                
                if intervals:
                    await self.db.bulk_insert("intervals", intervals)
                
                if intervals:
                    await self.db.bulk_insert("intervals", intervals)
                
                total_count = len(data)
                successful_count = len([item for item in data if self._validate_interval_item(item)])
                logger.info(f" Processed {successful_count}/{total_count} intervals successfully")
                return successful_count
        
        logger.error("Failed to fetch intervals data")
        return 0
    
    async def ingest_car_data(self, session_key: int):
        """Ingest car telemetry data"""
        # Car data API doesn't work well with session_key only (too much data)
        # Go directly to driver-specific approach
        logger.info("  📡 Car data requires driver-specific queries due to volume...")
        return await self._ingest_car_data_by_drivers(session_key)
    
    async def _ingest_car_data_by_drivers(self, session_key: int):
        """Fallback method: fetch car data for each driver individually"""
        # First get all drivers for this session
        drivers_url = f"{config.OPENF1_BASE_URL}/drivers?session_key={session_key}"
        
        async with self.session.get(drivers_url) as response:
            if response.status != 200:
                logger.error(" Failed to fetch drivers for car data ingestion")
                return 0
                
            drivers_data = await response.json()
            if not drivers_data:
                logger.warning(" No drivers found for this session")
                return 0
        
        total_car_data = 0
        logger.info(f" Found {len(drivers_data)} drivers, fetching car data for each...")

        # Fetch car data for each driver
        for i, driver in enumerate(drivers_data, 1):
            driver_number = driver.get('driver_number')
            if not driver_number:
                continue

            logger.debug(f" Fetching car data for driver {driver_number} ({i}/{len(drivers_data)})")

            # Use speed filters to avoid "too much data" errors
            driver_total = 0
            speed_filters = [
                "speed=0",
                "speed>=1&speed<150",
                "speed>=150&speed<350",
                "speed>=350"
            ]
            
            # Try each speed filter
            for speed_filter in speed_filters:
                car_data_url = f"{config.OPENF1_BASE_URL}/car_data?session_key={session_key}&driver_number={driver_number}&{speed_filter}"
                
                async with self.session.get(car_data_url) as driver_response:
                    if driver_response.status == 200:
                        driver_data = await driver_response.json()
                        if driver_data:
                            logger.debug(f" Got {len(driver_data)} records for driver {driver_number}")
                            processed_count = await self._process_car_data_batch(driver_data)
                            total_car_data += processed_count
                        else:
                            logger.debug(f" No car data for driver {driver_number}")
                    else:
                        logger.debug(f"  Failed to fetch car data for driver {driver_number}")

        if total_car_data > 0:
            logger.info(f" Processed {total_car_data} car data records across all drivers")
        else:
            logger.warning("  No car data available for this session (this is normal for some session types)")

        return total_car_data
    
    async def _process_car_data_batch(self, data: List[Dict]):
        """Process a batch of car data records"""
        car_data_records = []
        successful_count = 0
        
        for item in data:
            try:
                if isinstance(item.get('date'), str):
                    item['date'] = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
                
                car_data = CarData(**item)
                car_data_records.append(car_data.model_dump())
                successful_count += 1
                
                if len(car_data_records) >= config.BATCH_SIZE:
                    await self.db.bulk_insert("car_data", car_data_records)
                    car_data_records = []
                    
            except Exception as e:
                # Only show first 3 errors to avoid spam
                if successful_count < 3:
                    logger.warning(f"Error processing car data for driver {item.get('driver_number', 'unknown')}: {str(e)[:100]}...")
                elif successful_count == 3:
                    logger.warning("More car data validation errors found... (suppressing further messages)")
        
        # Insert remaining records
        if car_data_records:
            await self.db.bulk_insert("car_data", car_data_records)
        
        return successful_count
    
    def _validate_lap_item(self, item: dict) -> bool:
        """Check if a lap item can be validated without errors"""
        try:
            if isinstance(item.get('date_start'), str):
                item['date_start'] = datetime.fromisoformat(item['date_start'].replace('Z', '+00:00'))
            Lap(**item)
            return True
        except:
            return False
    
    def _validate_interval_item(self, item: dict) -> bool:
        """Check if an interval item can be validated without errors"""
        try:
            if isinstance(item.get('date'), str):
                item['date'] = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
            Interval(**item)
            return True
        except:
            return False
    
    def _validate_car_data_item(self, item: dict) -> bool:
        """Check if a car data item can be validated without errors"""
        try:
            if isinstance(item.get('date'), str):
                item['date'] = datetime.fromisoformat(item['date'].replace('Z', '+00:00'))
            CarData(**item)
            return True
        except:
            return False