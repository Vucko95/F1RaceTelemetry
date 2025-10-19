# F1 Race Telemetry Stats Explanation

## Stats for 1 Race

### Breakdown:
For a single race, the data is structured as follows:

- **Sessions**: 1 document
  - Example: `{ "session_key": 9158, "name": "Race", "location": "Monaco" }`

- **Drivers**: 20 documents (1 per driver)
  - Example: `{ "session_key": 9158, "driver_number": 1, "name": "Max Verstappen" }`

- **Laps**: ~1,380 documents (20 drivers × ~69 laps per race)
  - Example: `{ "session_key": 9158, "driver_number": 1, "lap_number": 1, "lap_time": 78.123 }`

- **Car Data**: ~600,000 documents (telemetry every ~0.27 seconds at 3.7Hz sample rate)
  - Example: `{ "session_key": 9158, "driver_number": 1, "date": "2024-05-26T14:01:23.1", "throttle": 85, "speed": 287, "rpm": 11000, "n_gear": 7, "brake": 0, "drs": 8 }`

- **Positions**: ~40,000 documents (position updates every few seconds)
  - Example: `{ "session_key": 9158, "driver_number": 1, "position": 1, "time": "2024-05-26T14:01:23" }`

- **Intervals**: ~20,000 documents (time gaps between drivers)
  - Example: `{ "session_key": 9158, "driver_number": 1, "gap_to_leader": 0.0, "time": "2024-05-26T14:01:23" }`

### Total Data Volume for 1 Race:
```json
{
    "sessions": 1,
    "drivers": 20,
    "laps": ~1,380,
    "car_data": ~562,674,
    "positions": ~40,000,
    "intervals": ~20,000
}
```

---

## Stats for the Whole Season

### Breakdown:
For an entire season (24 races), the data is structured as follows:

- **Sessions**: ~156 documents (6-7 sessions per race: Practice, Quali, Race, etc.)
  - Example: `{ "session_key": 9158, "name": "Race", "location": "Monaco" }`

- **Drivers**: ~3,120 documents (20 drivers × 156 sessions)
  - Example: `{ "session_key": 9158, "driver_number": 1, "name": "Max Verstappen" }`

- **Laps**: ~125,430 documents (~800 laps per session × 156 sessions)
  - Example: `{ "session_key": 9158, "driver_number": 1, "lap_number": 1, "lap_time": 78.123 }`

- **Car Data**: ~13,504,176 documents (telemetry at 3.7Hz sample rate × 24 races)
  - Example: `{ "session_key": 9158, "driver_number": 1, "date": "2024-05-26T14:01:23.1", "throttle": 85, "speed": 287, "rpm": 11000, "n_gear": 7, "brake": 0, "drs": 8 }`

- **Positions**: ~890,123 documents (position updates every few seconds × 24 races)
  - Example: `{ "session_key": 9158, "driver_number": 1, "position": 1, "time": "2024-05-26T14:01:23" }`

- **Intervals**: ~445,678 documents (time gaps between drivers × 24 races)
  - Example: `{ "session_key": 9158, "driver_number": 1, "gap_to_leader": 0.0, "time": "2024-05-26T14:01:23" }`

### Total Data Volume for the Whole Season:
```json
{
    "sessions": ~156,
    "drivers": ~3,120,
    "laps": ~125,430,
    "car_data": ~13,504,176,
    "positions": ~890,123,
    "intervals": ~445,678
}
```

---

## Additional Explanation: `meeting_key`

### What is `meeting_key`?
- The `meeting_key` is a unique identifier for an entire race weekend (or "meeting") that includes all sessions (Practice, Qualifying, Race, etc.) for a specific event.
- It groups all sessions under one umbrella, making it easier to query or analyze data for the entire event.

### Example:
For the Bahrain Grand Prix 2024:
```json
{
    "meeting_key": 1229,
    "session_key": 9472,
    "location": "Sakhir",
    "date_start": "2024-03-02T15:00:00+00:00",
    "date_end": "2024-03-02T17:00:00+00:00",
    "session_type": "Race",
    "session_name": "Race",
    "country_key": 36,
    "country_code": "BRN",
    "country_name": "Bahrain",
    "circuit_key": 63,
    "circuit_short_name": "Sakhir",
    "gmt_offset": "03:00:00",
    "year": 2024
}
```
- **`meeting_key`:** `1229` identifies the Bahrain GP 2024 as a whole.
- **`session_key`:** `9472` identifies the specific session (e.g., the Race).

### Relationship Between `meeting_key` and `session_key`:
- **`meeting_key`** groups all sessions (e.g., Practice, Qualifying, Race) for a single event.
- **`session_key`** identifies individual sessions within that event.

### Visual Representation:
```
Meeting Key: 1229 (Bahrain GP 2024)
├── Session Key: 9470 (Practice 1)
├── Session Key: 9471 (Qualifying)
└── Session Key: 9472 (Race)
```

---

## Visual Representation

### 1 Race:
```
Session Key: 9158 (Monaco GP 2024 - Race)
├── Sessions: 1 document
├── Drivers: 20 documents
├── Laps: ~1,380 documents
├── Car Data: ~562,674 documents
├── Positions: ~40,000 documents
└── Intervals: ~20,000 documents
```

### Whole Season:
```
Season 2024 (24 Races)
├── Sessions: ~156 documents
├── Drivers: ~3,120 documents
├── Laps: ~125,430 documents
├── Car Data: ~13,504,176 documents
├── Positions: ~890,123 documents
└── Intervals: ~445,678 documents
```