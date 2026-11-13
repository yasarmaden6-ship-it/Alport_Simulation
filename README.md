# Alport_Simulation

A simple port simulation built with SimPy for the IE401 capstone project. It demonstrates ship arrivals, server queues, and operations paused by rain.

## Setup and execution

The current configuration uses `ARRIVAL_RATE = 0.0164` ships per hour and `SIMULATION_HOURS = 1000`. Update these values in `config.py` when needed. Pass the positive, finite rate itself, not its reciprocal; the mean inter-arrival time is `1 / ARRIVAL_RATE` hours (about 60.98 hours with the current rate).

Then open a terminal in this directory and run:

```bash
python3 -m pip install -r requirements.txt
python3 baby_simulation.py
```

Checked with Python 3.13 and SimPy 4.1.2.

## Files

| File | Purpose |
|---|---|
| `baby_simulation.py` | Prepares the environment and shared rain schedule, then runs the model |
| `config.py` | Stores the server count, durations, arrival rate, and probabilities |
| `arrivals.py` | Generates continuous-time Poisson arrivals and samples a type after each arrival |
| `port.py` | Manages each ship's queueing, operation, and departure |
| `results.py` | Prints ship counts and durations |

## Model rules

- There are three servers, each representing one port service position and serving one ship at a time
- Each ship requires 100 net working hours
- Arrivals follow a homogeneous Poisson process with constant rate `ARRIVAL_RATE`
- Each inter-arrival time is drawn using `random.expovariate(ARRIVAL_RATE)`; the first ship arrives after the first sampled wait
- Time is measured in hours and can be fractional; for example, 0.25 hours is 15 minutes
- More than one ship can arrive within an hour; ships are served in arrival order
- After each arrival, a separate Uniform(0,1) draw assigns `dry_cargo` if the value is below 0.66, otherwise `container`
- Ship type is stored in the ship's record and does not yet affect operation or rain handling
- Rain still uses a shared hourly schedule with rain probability 0.329
- Rain affects the whole port; ships keep their servers but make no progress
- Work resumes from the remaining workload when the weather becomes dry
- The port starts empty; the observation period is `0 <= hour < SIMULATION_HOURS` (currently 1000 hours)
- `SEED = 43` reproduces the same random scenario with the same settings

The model uses the values in `config.py` without reading any data files. The configured arrival rate is 0.0164 ships per hour; the ship-type probability and operating rules are assumptions for this example model.

The existing operation loop still checks rain at the start of each ship's one-hour step. Exact handling of weather-change times and the external weather data are outside this arrivals update.

## Results

The program prints the numbers of arrived, departed, queued, and currently assigned ships. Average queue time is calculated for all ships that have been assigned a server; average port stay is calculated for ships that have departed. Rain delays are also shown for departed ships. `server_assignment_time` records when a ship gets a server, even if rain prevents work from starting immediately.

Ship records also contain `ship_type`; the current console report does not display it. The output table aligns columns and displays times to two decimal places; calculations retain full precision.
