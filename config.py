# All durations are in hours; each berth serves one ship at a time.
BERTH_COUNT = 3
OPERATION_HOURS = 100  # Net working hours required per ship, excluding rain
SIMULATION_HOURS = 720

# Arrivals and rain use separate random draws each hour.
ARRIVAL_PROBABILITY = 0.01575
RAIN_PROBABILITY = 0.329

# Reproduce the same random scenario when running with the same settings.
SEED = 42
