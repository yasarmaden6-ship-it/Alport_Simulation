from math import isfinite

from config import OPERATION_HOURS
from results import print_event


class Port:
    def __init__(
        self, env, capacity, weather, log_events=False,
        operation_hours=None, end_hour=None
    ):
        if capacity <= 0:
            raise ValueError("Port capacity must be greater than zero.")

        if operation_hours is None:
            operation_hours = OPERATION_HOURS

        if not isfinite(operation_hours) or operation_hours <= 0:
            raise ValueError("Operation hours must be a positive finite number.")

        self.env = env
        self.capacity = capacity
        self.weather = weather
        self.operation_hours = operation_hours
        self.end_hour = end_hour
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
            "operation_hours": self.operation_hours,
        }
        self.records.append(record)
        self.waiting_ships.append(record)
        self._dispatch()

        if record["server_assignment_time"] is None:
            self.env.process(self._report_waiting(record))

    def _report_waiting(self, record):
        yield self.env.timeout(0)

        if record["server_assignment_time"] is not None:
            return

        if len(self.waiting_ships) > self.peak_queue_size:
            self.peak_queue_size = len(self.waiting_ships)
            self.peak_queue_time = self.env.now

        self._report("QUEUED", record)

    def _report(self, event=None, record=None):
        if not self.log_events:
            return

        wet, _ = self.weather.at(self.env.now)

        if self._reported_wet is None:
            print_event(self, "START")
        elif wet != self._reported_wet:
            print_event(self, "RAIN STARTED" if wet else "RAIN ENDED")

        self._reported_wet = wet

        if event is not None:
            print_event(self, event, record)

    def _dispatch(self):
        self._report()

        if self.end_hour is not None and self.env.now + self.operation_hours > self.end_hour:
            return

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

            event = (
                "ARRIVED/STARTED"
                if record["arrival_time"] == self.env.now
                else "TAKEN FROM QUEUE"
            )
            self._report(event, record)
            self.env.process(self._serve(record))

    def _serve(self, record):
        record["rain_wait_time"] = 0.0

        if record["ship_type"] == "dry_cargo":
            hour = record["arrival_time"]
            start = record["server_assignment_time"]

            while hour < start:
                wet, next_change = self.weather.at(hour)
                interval_end = min(next_change, start)

                if wet:
                    record["rain_wait_time"] += interval_end - hour

                hour = interval_end

        yield self.env.timeout(record["operation_hours"])

        self._report()
        record["departure_time"] = self.env.now
        self.busy_berths -= 1
        self._report("DEPARTED", record)
        self._dispatch()

    def _watch_weather(self):
        for change in self.weather.transitions:
            yield self.env.timeout(change - self.env.now)
            self._dispatch()