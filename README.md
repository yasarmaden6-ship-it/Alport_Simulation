# Alport_Simulation

A simple port simulation built with SimPy for the IE401 capstone project. It demonstrates ship arrivals, berth queues, and operations paused by rain.

## Setup and execution

Open a terminal in this directory and run:

```bash
python3 -m pip install -r requirements.txt
python3 baby_simulation.py
```

Checked with Python 3.13 and SimPy 4.1.2.

## Files

| File | Purpose |
|---|---|
| `baby_simulation.py` | Prepares the environment and shared rain schedule, then runs the model |
| `config.py` | Stores the berth count, durations, and probabilities |
| `arrivals.py` | Generates hourly ship arrivals |
| `port.py` | Manages each ship's queueing, operation, and departure |
| `results.py` | Prints ship counts and durations |

## Model rules

- There are three berths, each serving one ship at a time
- There is one ship type; each ship requires 100 net working hours
- Rain and arrivals use separate Uniform(0,1) draws each hour
- The hourly arrival probability is 0.01575 and the rain probability is 0.329
- At most one ship arrives per hour; ships are served in arrival order
- Rain affects the whole port; ships keep their berths but make no progress
- Work resumes from the remaining workload when the weather becomes dry
- The port starts empty; the observation period is `0 <= hour < 720`
- `SEED = 42` reproduces the same random scenario with the same settings

The model uses the values in `config.py` without reading any data files. The probabilities and operating rules are assumptions for this example model.

## Results

The program prints the numbers of arrived, departed, queued, and berthed ships. Average queue time is calculated for ships that have berthed; average port stay is calculated for ships that have departed. Rain delays are also shown for departed ships.

With the default settings, the checked example run produces 8 arrivals, 7 departures, and 1 ship remaining at a berth. Average queue time is 2.62 hours, and average port stay for departed ships is 153 hours.
