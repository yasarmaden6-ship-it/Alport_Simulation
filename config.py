# All durations are in hours; each server serves one ship at a time.
SERVER_COUNT = 3
OPERATION_HOURS = 200  # Uninterrupted service hours per ship after berth admission
SIMULATION_HOURS = 2232

# Set the measured arrival rate in ships per hour before running the model.
ARRIVAL_RATE = 0.0164
DRY_CARGO_PROBABILITY = 0.66


# Reproduce the same random scenario when running with the same settings.
SEED = 1

# UTC calendar anchor for the seasonal spline.
from datetime import datetime, timezone

SIMULATION_START = datetime(2026, 11, 25, tzinfo=timezone.utc)
INITIAL_WET = False
WEATHER_SEED = 2
