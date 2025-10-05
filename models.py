from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List, Union
from bson import ObjectId

class BaseF1Model(BaseModel):
    """Base model for all F1 data"""
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class CarData(BaseF1Model):
    """Car telemetry data - ~3.7Hz sample rate"""
    session_key: int
    meeting_key: Optional[int] = None
    driver_number: int
    date: datetime
    rpm: Optional[int] = None
    speed: Optional[int] = None
    n_gear: Optional[int] = None
    throttle: Optional[float] = None
    brake: Optional[int] = None
    drs: Optional[int] = None

class Meeting(BaseF1Model):
    """F1 Meeting/Weekend data"""
    meeting_key: int
    meeting_name: str
    meeting_official_name: str
    location: str
    country_key: int
    country_code: str
    country_name: str
    circuit_key: int
    circuit_short_name: str
    date_start: datetime
    gmt_offset: str
    year: int

class Session(BaseF1Model):
    """Session data (Practice, Qualifying, Race, etc.)"""
    session_key: int
    session_name: str
    session_type: str
    meeting_key: int
    location: str
    country_key: int
    country_code: str
    country_name: str
    circuit_key: int
    circuit_short_name: str
    date_start: datetime
    date_end: datetime
    gmt_offset: str
    year: int

class Driver(BaseF1Model):
    """Driver information"""
    session_key: int
    meeting_key: Optional[int] = None
    driver_number: int
    broadcast_name: Optional[str] = None
    country_code: Optional[str] = None
    first_name: Optional[str] = None
    full_name: Optional[str] = None
    last_name: Optional[str] = None
    team_colour: Optional[str] = None
    team_name: Optional[str] = None
    name_acronym: Optional[str] = None
    headshot_url: Optional[str] = None

class Lap(BaseF1Model):
    """Lap timing data"""
    session_key: int
    meeting_key: Optional[int] = None
    driver_number: int
    date_start: Optional[datetime] = None
    lap_number: int
    lap_duration: Optional[float] = None
    is_pit_out_lap: Optional[bool] = None
    stint_number: Optional[int] = None
    # Sector durations
    duration_sector_1: Optional[float] = None
    duration_sector_2: Optional[float] = None
    duration_sector_3: Optional[float] = None
    # Speed trap data
    i1_speed: Optional[int] = None  # Intermediate 1 speed
    i2_speed: Optional[int] = None  # Intermediate 2 speed
    st_speed: Optional[int] = None  # Speed trap speed
    # Allow mixed types in segments - can contain None values
    segments_sector_1: Optional[List[Optional[int]]] = None
    segments_sector_2: Optional[List[Optional[int]]] = None
    segments_sector_3: Optional[List[Optional[int]]] = None
    sectors_sector_1: Optional[float] = None
    sectors_sector_2: Optional[float] = None
    sectors_sector_3: Optional[float] = None

class Position(BaseF1Model):
    """Driver position data"""
    session_key: int
    meeting_key: Optional[int] = None
    driver_number: int
    date: datetime
    position: int

class Interval(BaseF1Model):
    """Gap between drivers"""
    session_key: int
    meeting_key: Optional[int] = None
    driver_number: int
    date: datetime
    gap_to_leader: Optional[Union[float, str]] = None  # Can be float or string like "+1 LAP"
    interval: Optional[Union[float, str]] = None  # Can be float or string
    
    @field_validator('gap_to_leader', 'interval', mode='before')
    @classmethod
    def parse_gap_values(cls, v):
        """Parse gap values - keep strings like '+1 LAP' as is, convert numbers to float"""
        if v is None:
            return None
        if isinstance(v, str):
            # Try to convert to float first
            try:
                return float(v)
            except (ValueError, TypeError):
                # If it fails, keep as string (e.g., "+1 LAP", "+2 LAPS")
                return v
        try:
            return float(v)
        except (ValueError, TypeError):
            return v

class PitStop(BaseF1Model):
    """Pit stop data"""
    session_key: int
    driver_number: int
    date: datetime
    lap_number: int
    pit_duration: Optional[float] = None

class RaceControl(BaseF1Model):
    """Race control messages"""
    session_key: int
    date: datetime
    lap_number: Optional[int] = None
    message: str
    flag: Optional[str] = None
    scope: Optional[str] = None
    sector: Optional[int] = None
    driver_number: Optional[int] = None

class TeamRadio(BaseF1Model):
    """Team radio communications"""
    session_key: int
    driver_number: int
    date: datetime
    recording_url: str

class Weather(BaseF1Model):
    """Weather conditions"""
    session_key: int
    date: datetime
    air_temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    rainfall: Optional[int] = None
    track_temperature: Optional[float] = None
    wind_direction: Optional[int] = None
    wind_speed: Optional[float] = None

class Location(BaseF1Model):
    """Driver location on track"""
    session_key: int
    driver_number: int
    date: datetime
    x: int
    y: int
    z: int