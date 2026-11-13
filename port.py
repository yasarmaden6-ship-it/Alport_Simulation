from config import OPERATION_HOURS
from results import print_event


class Port:
    """Assign free berths in arrival order, skipping dry cargo during rain."""

    def __init__(self, env, capacity, weather, log_events=False):
        if capacity <= 0:
            raise ValueError("Port capacity must be greater than zero.")
        self.env = env
        self.capacity = capacity
        self.weather = weather
        self.waiting_ships = []
        self.busy_berths = 0
        self.records = []
        self.peak_queue_size = 0
        self.peak_queue_time = None
        self.log_events = log_events
        self._reported_wet = None
        self._report()
        env.process(self._watch_weather())

    def arrive(self, ship_id, ship_type):
        self._report()
        record = {
            "ship_id": ship_id,
            "ship_type": ship_type,
            "arrival_time": self.env.now,
            "server_assignment_time": None,
            "departure_time": None,
            "rain_wait_time": None,
        }
        self.records.append(record)
        self.waiting_ships.append(record)
        self._dispatch()
        if record["server_assignment_time"] is None:
            self.env.process(self._report_waiting(record))

    # Let same-time departures and weather changes settle before counting a wait.
    def _report_waiting(self, record):
        yield self.env.timeout(0)
        if record["server_assignment_time"] is not None:
            return
        if len(self.waiting_ships) > self.peak_queue_size:
            self.peak_queue_size = len(self.waiting_ships)
            self.peak_queue_time = self.env.now
        self._report("KUYRUKTA", record)

    # Announce weather before same-time ship events, regardless of callback order.
    def _report(self, event=None, record=None):
        if not self.log_events:
            return
        wet, _ = self.weather.at(self.env.now)
        if self._reported_wet is None:
            print_event(self, "BAŞLANGIÇ")
        elif wet != self._reported_wet:
            print_event(self, "YAĞMUR BAŞLADI" if wet else "YAĞMUR BİTTİ")
        self._reported_wet = wet
        if event is not None:
            print_event(self, event, record)

    # Keep the original queue order and reserve each berth before starting work.
    def _dispatch(self):
        self._report()
        wet, _ = self.weather.at(self.env.now)
        while self.busy_berths < self.capacity:
            record = next(
                (
                    ship for ship in self.waiting_ships
                    if not wet or ship["ship_type"] == "container"
                ),
                None,
            )
            if record is None:
                return
            self.waiting_ships.remove(record)
            record["server_assignment_time"] = self.env.now
            self.busy_berths += 1
            event = "GELDİ/BAŞLADI" if record["arrival_time"] == self.env.now else "SIRADAN ALINDI"
            self._report(event, record)
            self.env.process(self._serve(record))

    # Measure rainy queue time only; an admitted ship works without interruption.
    def _serve(self, record):
        record["rain_wait_time"] = 0.0
        if record["ship_type"] == "dry_cargo":
            hour = record["arrival_time"]
            while hour < record["server_assignment_time"]:
                wet, next_change = self.weather.at(hour)
                end = min(next_change, record["server_assignment_time"])
                if wet:
                    record["rain_wait_time"] += end - hour
                hour = end

        yield self.env.timeout(OPERATION_HOURS)
        self._report()
        record["departure_time"] = self.env.now
        self.busy_berths -= 1
        self._report("AYRILDI", record)
        self._dispatch()

    # Reconsider waiting ships at every weather transition, even with no arrivals.
    def _watch_weather(self):
        for change in self.weather.transitions:
            yield self.env.timeout(change - self.env.now)
            self._dispatch()
