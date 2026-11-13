# All durations are in hours; each server serves one ship at a time.
SERVER_COUNT = 3
OPERATION_HOURS = 100  # Net working hours required per ship, excluding rain
SIMULATION_HOURS = 1000

# Set the measured arrival rate in ships per hour before running the model.
ARRIVAL_RATE = 0.0164
DRY_CARGO_PROBABILITY = 0.66

# Rain is still sampled once per hour for the shared schedule.
RAIN_PROBABILITY = 0.329

# Reproduce the same random scenario when running with the same settings.
SEED = 43
