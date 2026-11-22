# Alport Simulation

SimPy port model with continuous-time ship arrivals and a shared seasonal CTMC weather path.

## Run

```bash
python -m pip install -r requirements.txt
python simulation.py
```

Keep the bundled Excel workbook beside weather.py. Set the hourly arrival rate in config.py if your estimated rate changes. The current rate is 0.0164 ships per hour.

## Model

- The run starts on 25 November at 00:00 UTC and covers 2,232 hours, including all of 25 February. The calendar anchor uses 2026–2027.
- weather.py reads the 12 monthly knots from the 0.1 mm spline workbook and generates one shared path using integrated transition hazards. Transition times may be fractional hours. The initial weather state is dry. WEATHER_SEED controls the path independently of the arrival seed.
- Arrivals are homogeneous Poisson. The existing dry cargo share is 0.66. Three berths serve ships for 100 uninterrupted hours each after admission, regardless of later weather changes.
- All waiting ships stay in one queue in their original arrival order. Equal-time arrivals keep their registration order. In dry weather, each free berth takes the first waiting ship (FCFS).
- During rain, dry cargo stays in the queue without losing its place. Free berths take the earliest waiting container ships. Ships already admitted, including dry cargo, finish their work without interruption.
- When rain ends, free berths immediately resume FCFS across all waiting ships. Work already in progress is never preempted. Admission uses the weather at that exact time: rain start blocks new dry cargo; rain end allows it.
- Arrival and berth assignment are recorded separately. `rain_wait_time` (shown as `Yağmur` in the final table) measures a dry cargo ship's queue time overlapping rain, including periods when all berths are busy. It is part of total time to berth, not an additional delay or an estimate of delay caused solely by rain. It is zero for containers and is calculated on admission; ships still waiting have no value yet. Rain during service is excluded.
- The report includes arrivals in the half-open interval `[0, SIMULATION_HOURS)`. Events exactly at the horizon are not processed. Average port stay and detailed rainy queue waits use departed ships.

## Terminal output

`python simulation.py` prints a Turkish event timeline while the simulation runs, followed by a summary and departed-ship details. Each event is flushed immediately; simulation time advances as fast as SimPy runs, without real-time sleeps.

- `Gün` starts at 1: hours `[0, 24)` are day 1, `[24, 48)` are day 2. `Saat` is total elapsed simulation hours, displayed to two decimals; the model still uses exact fractional times.
- `Hava`, `Olay`, and `Gemi` show rain start/end, admission, queue entry, and departure. `Rıhtım` shows occupied/total berths. `Kuyruk`, `Kuru`, and `Kont` show waiting ships, split by cargo type, at that event.
- Immediate admission is one `GELDİ/BAŞLADI` event, not artificial queue buildup. `SIRADAN ALINDI` shows the actual wait and whether the queue emptied. `KUYRUKTA` explains rain restrictions and/or full berths.
- Weather changes are announced once, before ship events at the same time. Rain ending reopens FCFS admission; the next actual admission is shown separately, since berths may still be full.
- Queue-entry messages and peak counts wait for same-time arrivals, departures, and weather callbacks to finish; a ship admitted at its arrival time does not create a false queue peak. Individual service/departure rows show the state at that event. The summary reports the highest waiting queue and the first time it occurred. A run ending at hour 2232 reports 93 observed days, without creating an event on day 94.
- `Port(..., log_events=False)` keeps programmatic runs quiet; the main script enables the timeline. Logging does not change scheduling or random draws.

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests use fixed arrival times and weather transitions to check FCFS, rain admission, uninterrupted service, berth capacity, simultaneous events, the simulation horizon, and terminal event accuracy.
