import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import simpy

from port import Port
from results import print_results
from weather import WeatherCalendar


# Read event columns while ignoring headers and the separate departure table.
def event_rows(output):
    rows = []
    for line in output.splitlines():
        fields = [field.strip() for field in line.split("|")]
        if len(fields) == 10 and fields[0].isdigit():
            rows.append({
                "day": int(fields[0]),
                "hour": float(fields[1]),
                "weather": fields[2],
                "event": fields[3],
                "ship": fields[4],
                "occupancy": fields[5],
                "queue": int(fields[6]),
                "dry": int(fields[7]),
                "containers": int(fields[8]),
                "detail": fields[9],
            })
    return rows


class TerminalOutputTests(unittest.TestCase):
    def setUp(self):
        operation_hours = patch("port.OPERATION_HOURS", 10)
        operation_hours.start()
        self.addCleanup(operation_hours.stop)

    def run_scenario(
        self, arrivals=(), transitions=(), initial_wet=False,
        capacity=1, until=60, log_events=True,
    ):
        env = simpy.Environment()
        output = io.StringIO()
        with redirect_stdout(output):
            port = Port(
                env, capacity, WeatherCalendar(list(transitions), initial_wet, until),
                log_events=log_events,
            )

            def arrival_process():
                for hour, ship_id, ship_type in arrivals:
                    yield env.timeout(hour - env.now)
                    port.arrive(ship_id, ship_type)

            env.process(arrival_process())
            env.run(until=until)
            print_results(port)
        return port, output.getvalue()

    def test_immediate_admission_does_not_report_a_queue(self):
        port, output = self.run_scenario([(0, 1, "dry_cargo")], until=20)
        rows = event_rows(output)
        self.assertEqual(
            [row["event"] for row in rows],
            ["BAŞLANGIÇ", "GELDİ/BAŞLADI", "AYRILDI"],
        )
        self.assertTrue(all(row["queue"] == 0 for row in rows))
        self.assertIn("Bekleme: 0.00 sa", rows[1]["detail"])
        self.assertEqual(port.peak_queue_size, 0)
        self.assertIsNone(port.peak_queue_time)
        self.assertIn("En yüksek kuyruk: 0 gemi", output)

    def test_arrival_at_completion_time_does_not_create_a_zero_duration_queue(self):
        for arrival_first in [False, True]:
            with self.subTest(arrival_first=arrival_first):
                env = simpy.Environment()
                output = io.StringIO()

                def second_arrival():
                    yield env.timeout(10)
                    port.arrive(2, "container")

                with redirect_stdout(output):
                    port = Port(env, 1, WeatherCalendar([], False, 30), log_events=True)
                    if arrival_first:
                        env.process(second_arrival())
                    port.arrive(1, "container")
                    if not arrival_first:
                        env.process(second_arrival())
                    env.run(until=30)
                self.assertEqual(
                    [ship["server_assignment_time"] - ship["arrival_time"]
                     for ship in port.records],
                    [0, 0],
                )
                second_ship_events = [
                    row for row in event_rows(output.getvalue()) if row["ship"] == "2/KONT"
                ]
                admissions = [
                    row for row in second_ship_events
                    if row["event"] in ("GELDİ/BAŞLADI", "SIRADAN ALINDI")
                ]
                self.assertEqual(len(admissions), 1)
                self.assertEqual((port.peak_queue_size, port.peak_queue_time), (0, None))
                self.assertFalse(any(row["event"] == "KUYRUKTA" for row in second_ship_events))

    def test_queue_buildup_and_recovery_are_visible_without_false_rain_resume(self):
        port, output = self.run_scenario(
            [(0, 1, "dry_cargo"), (3, 2, "dry_cargo"),
             (4, 3, "container"), (5, 4, "dry_cargo"), (6, 5, "container")],
            transitions=[2, 26],
        )
        rows = event_rows(output)
        queued = [row for row in rows if row["event"] == "KUYRUKTA"]
        self.assertEqual([row["queue"] for row in queued], [1, 2, 3, 4])
        self.assertEqual((port.peak_queue_size, port.peak_queue_time), (4, 6))
        self.assertIn("yağmur", queued[0]["detail"])
        self.assertIn("rıhtımlar dolu", queued[0]["detail"])
        admitted = [row for row in rows if row["event"] == "SIRADAN ALINDI"]
        self.assertEqual(
            [(row["hour"], row["ship"], row["queue"]) for row in admitted],
            [(10, "3/KONT", 3), (20, "5/KONT", 2),
             (30, "2/KURU", 1), (40, "4/KURU", 0)],
        )
        rain_end = next(row for row in rows if row["event"] == "YAĞMUR BİTTİ")
        self.assertEqual((rain_end["day"], rain_end["hour"]), (2, 26))
        self.assertEqual((rain_end["occupancy"], rain_end["queue"]), ("1/1", 2))
        self.assertIn("FCFS yeniden açık", rain_end["detail"])
        self.assertIn("Bekleme: 27.00 sa", admitted[2]["detail"])
        self.assertIn("kuyruk boşaldı", admitted[-1]["detail"])
        self.assertIn("En yüksek kuyruk: 4 gemi (ilk kez Gün 1, saat 6.00)", output)

    def test_weather_markers_precede_boundary_ship_events_in_either_callback_order(self):
        for arrivals_first in [False, True]:
            with self.subTest(arrivals_first=arrivals_first):
                env = simpy.Environment()
                output = io.StringIO()

                def boundary_arrivals():
                    yield env.timeout(10)
                    port.arrive(1, "dry_cargo")
                    port.arrive(2, "container")
                    yield env.timeout(10)
                    port.arrive(3, "dry_cargo")

                with redirect_stdout(output):
                    if arrivals_first:
                        env.process(boundary_arrivals())
                    port = Port(env, 3, WeatherCalendar([10, 20], False, 40), log_events=True)
                    if not arrivals_first:
                        env.process(boundary_arrivals())
                    env.run(until=40)
                rows = event_rows(output.getvalue())
                for hour, event, weather in [
                    (10, "YAĞMUR BAŞLADI", "YAĞMUR"),
                    (20, "YAĞMUR BİTTİ", "KURU"),
                ]:
                    at_boundary = [row for row in rows if row["hour"] == hour]
                    self.assertEqual(at_boundary[0]["event"], event)
                    self.assertEqual(sum(row["event"] == event for row in rows), 1)
                    self.assertTrue(all(row["weather"] == weather for row in at_boundary))
                self.assertEqual(
                    [ship["server_assignment_time"] for ship in port.records], [20, 10, 20]
                )

    def test_weather_markers_precede_same_time_completions(self):
        # The first transition changes the scheduling order of the event at 10.
        for initial_wet, transitions in [(False, [10, 20]), (True, [1, 10, 20])]:
            with self.subTest(initial_wet=initial_wet):
                _, output = self.run_scenario(
                    [(0, 1, "container"), (2, 2, "dry_cargo"), (3, 3, "container")],
                    transitions=transitions, initial_wet=initial_wet,
                )
                rows = event_rows(output)
                for hour, event in [(10, "YAĞMUR BAŞLADI"), (20, "YAĞMUR BİTTİ")]:
                    at_boundary = [row for row in rows if row["hour"] == hour]
                    self.assertEqual(at_boundary[0]["event"], event)
                    self.assertIn("AYRILDI", [row["event"] for row in at_boundary])
                    self.assertIn("SIRADAN ALINDI", [row["event"] for row in at_boundary])

    def test_day_column_changes_at_hour_24(self):
        _, output = self.run_scenario(
            [(23.99, 1, "container"), (24, 2, "dry_cargo")], capacity=2, until=40
        )
        admissions = [row for row in event_rows(output) if row["event"] == "GELDİ/BAŞLADI"]
        self.assertEqual(
            [(row["day"], row["hour"]) for row in admissions], [(1, 23.99), (2, 24)]
        )

    def test_horizon_summary_does_not_create_a_day_94_event(self):
        _, output = self.run_scenario(
            [(2231, 1, "container")], transitions=[2232], until=2232
        )
        rows = event_rows(output)
        self.assertEqual(rows[-1]["day"], 93)
        self.assertTrue(all(row["hour"] < 2232 and row["day"] <= 93 for row in rows))
        self.assertFalse(any(row["event"] == "YAĞMUR BAŞLADI" for row in rows))
        self.assertIn("Gözlem süresi: 93.00 gün (0 <= saat < 2232)", output)
        self.assertIn("Hizmetteki gemi: 1", output)

    def test_every_event_has_consistent_queue_counts_and_occupancy(self):
        _, output = self.run_scenario(
            [(0, 1, "dry_cargo"), (0, 2, "container"), (1, 3, "dry_cargo"),
             (2, 4, "container"), (3, 5, "dry_cargo"), (4, 6, "container")],
            transitions=[0.5, 25], capacity=2,
        )
        rows = event_rows(output)
        self.assertTrue(any(row["queue"] > 1 for row in rows))
        for row in rows:
            with self.subTest(hour=row["hour"], event=row["event"], ship=row["ship"]):
                self.assertEqual(row["queue"], row["dry"] + row["containers"])
                busy, capacity = map(int, row["occupancy"].split("/"))
                self.assertGreaterEqual(busy, 0)
                self.assertLessEqual(busy, capacity)
                if row["weather"] == "YAĞMUR" and row["event"] in ("GELDİ/BAŞLADI", "SIRADAN ALINDI"):
                    self.assertTrue(row["ship"].endswith("/KONT"))

    def test_logging_does_not_change_the_simulation(self):
        arrivals = [(0, 1, "dry_cargo"), (3, 2, "dry_cargo"),
                    (4, 3, "container"), (5, 4, "dry_cargo"), (6, 5, "container")]
        logged, output = self.run_scenario(arrivals, transitions=[2, 26], log_events=True)
        silent, silent_output = self.run_scenario(arrivals, transitions=[2, 26], log_events=False)
        self.assertEqual(logged.records, silent.records)
        self.assertEqual(logged.waiting_ships, silent.waiting_ships)
        self.assertEqual(logged.busy_berths, silent.busy_berths)
        self.assertEqual(
            (logged.peak_queue_size, logged.peak_queue_time),
            (silent.peak_queue_size, silent.peak_queue_time),
        )
        self.assertTrue(event_rows(output))
        self.assertEqual(event_rows(silent_output), [])

    def test_initial_rain_and_empty_port_are_reported_without_fake_ship_events(self):
        port, output = self.run_scenario(initial_wet=True, transitions=[5], until=20)
        rows = event_rows(output)
        self.assertEqual([row["event"] for row in rows], ["BAŞLANGIÇ", "YAĞMUR BİTTİ"])
        self.assertEqual(rows[0]["weather"], "YAĞMUR")
        self.assertIn("Yalnızca konteyner kabulü açık", rows[0]["detail"])
        self.assertTrue(all(row["ship"] == "-" and row["queue"] == 0 for row in rows))
        self.assertEqual(port.records, [])
        self.assertIn("Gelen gemi: 0", output)
        self.assertIn("henüz ayrılan gemi yok", output)


if __name__ == "__main__":
    unittest.main()
