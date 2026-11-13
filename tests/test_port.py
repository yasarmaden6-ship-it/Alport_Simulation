import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import simpy

from arrivals import generate_arrivals
from port import Port
from results import print_results
from weather import WeatherCalendar


def arrive_at(env, port, hour, ship_id, ship_type):
    yield env.timeout(hour)
    port.arrive(ship_id, ship_type)


class PortPolicyTests(unittest.TestCase):
    def setUp(self):
        operation_hours = patch("port.OPERATION_HOURS", 10)
        operation_hours.start()
        self.addCleanup(operation_hours.stop)

    # Check conservation and admission rules after every simulated event.
    def run_until(self, env, port, until):
        while env.peek() < until:
            env.step()
            assigned = [
                ship for ship in port.records
                if ship["server_assignment_time"] is not None
            ]
            departed = [
                ship for ship in assigned if ship["departure_time"] is not None
            ]
            self.assertEqual(len(assigned) - len(departed), port.busy_berths)
            self.assertEqual(
                len(port.records),
                len(departed) + port.busy_berths + len(port.waiting_ships),
            )
            self.assertLessEqual(port.busy_berths, port.capacity)
            self.assertGreaterEqual(port.busy_berths, 0)
            self.assertTrue(all(
                ship["server_assignment_time"] is None
                for ship in port.waiting_ships
            ))
            for ship in assigned:
                if ship["ship_type"] == "dry_cargo":
                    wet, _ = port.weather.at(ship["server_assignment_time"])
                    self.assertFalse(wet)
            for ship in departed:
                self.assertEqual(
                    ship["departure_time"] - ship["server_assignment_time"], 10
                )
        env.run(until=until)

    def run_scenario(
        self, arrivals, transitions=(), initial_wet=False, capacity=1, until=60
    ):
        env = simpy.Environment()
        weather = WeatherCalendar(list(transitions), initial_wet, until)
        port = Port(env, capacity, weather)
        for hour, ship_id, ship_type in arrivals:
            env.process(arrive_at(env, port, hour, ship_id, ship_type))
        self.run_until(env, port, until)
        return port

    def test_no_rain_preserves_fcfs_across_ship_types(self):
        port = self.run_scenario([
            (0, 1, "dry_cargo"), (1, 2, "container"), (2, 3, "dry_cargo")
        ])
        self.assertEqual(
            [(ship["server_assignment_time"], ship["departure_time"])
             for ship in port.records],
            [(0, 10), (10, 20), (20, 30)],
        )

    def test_rain_selects_containers_in_their_arrival_order(self):
        port = self.run_scenario(
            [(0, 1, "dry_cargo"), (1, 2, "container"),
             (2, 3, "dry_cargo"), (3, 4, "container")],
            transitions=[25], initial_wet=True,
        )
        self.assertEqual(
            [ship["server_assignment_time"] for ship in port.records],
            [25, 1, 35, 11],
        )

    def test_rain_end_restores_original_order_without_interrupting_container(self):
        port = self.run_scenario(
            [(0, 1, "dry_cargo"), (1, 2, "container"),
             (2, 3, "dry_cargo"), (3, 4, "container")],
            transitions=[8], initial_wet=True,
        )
        self.assertEqual(
            [(ship["server_assignment_time"], ship["departure_time"])
             for ship in port.records],
            [(11, 21), (1, 11), (21, 31), (31, 41)],
        )

    def test_admitted_dry_cargo_continues_through_repeated_rain(self):
        port = self.run_scenario(
            [(0, 1, "dry_cargo")], transitions=[2, 4, 6, 15], until=20
        )
        self.assertEqual(port.records[0]["departure_time"], 10)
        self.assertEqual(port.records[0]["rain_wait_time"], 0)

    def test_three_occupied_berths_finish_dry_work_before_taking_containers(self):
        port = self.run_scenario(
            [(0, 1, "dry_cargo"), (0, 2, "dry_cargo"),
             (0, 3, "dry_cargo"), (2, 4, "container"),
             (2, 5, "container"), (3, 6, "dry_cargo")],
            transitions=[1, 20], capacity=3,
        )
        self.assertEqual(
            [ship["server_assignment_time"] for ship in port.records],
            [0, 0, 0, 10, 10, 20],
        )
        self.assertEqual(
            [ship["departure_time"] for ship in port.records[:3]], [10, 10, 10]
        )

    def test_completion_at_rain_boundaries_uses_current_weather(self):
        # An earlier transition reverses weather/completion callback order at 10.
        for initial_wet, transitions in [(False, [10, 20]), (True, [1, 10, 20])]:
            with self.subTest(initial_wet=initial_wet):
                port = self.run_scenario(
                    [(0, 1, "container"), (2, 50, "dry_cargo"),
                     (3, 3, "container"), (20, 2, "dry_cargo")],
                    transitions=transitions, initial_wet=initial_wet,
                )
                self.assertEqual(
                    [ship["server_assignment_time"] for ship in port.records],
                    [0, 20, 10, 30],
                )

    def test_boundary_arrivals_work_before_or_after_weather_callback(self):
        for arrivals_first in [False, True]:
            with self.subTest(arrivals_first=arrivals_first):
                env = simpy.Environment()
                weather = WeatherCalendar([10, 20], False, 40)

                def boundary_arrivals():
                    yield env.timeout(10)
                    port.arrive(30, "dry_cargo")
                    port.arrive(20, "container")
                    yield env.timeout(10)
                    port.arrive(10, "dry_cargo")

                if arrivals_first:
                    env.process(boundary_arrivals())
                port = Port(env, 3, weather)
                if not arrivals_first:
                    env.process(boundary_arrivals())
                self.run_until(env, port, 40)
                self.assertEqual(
                    [ship["server_assignment_time"] for ship in port.records],
                    [20, 10, 20],
                )
                self.assertEqual(
                    [ship["rain_wait_time"] for ship in port.records], [10, 0, 0]
                )

    def test_equal_arrival_times_preserve_entry_order_not_ship_id_order(self):
        port = self.run_scenario([
            (0, 9, "container"), (1, 30, "dry_cargo"),
            (1, 2, "container"), (1, 1, "dry_cargo"),
        ])
        self.assertEqual(
            [ship["server_assignment_time"] for ship in port.records],
            [0, 10, 20, 30],
        )

    def test_continuous_rain_retains_dry_cargo_and_reports_actual_queue(self):
        port = self.run_scenario(
            [(0, 1, "dry_cargo"), (1, 2, "dry_cargo"),
             (2, 3, "container"), (3, 4, "container")],
            initial_wet=True, capacity=3, until=20,
        )
        self.assertEqual([ship["ship_id"] for ship in port.waiting_ships], [1, 2])
        self.assertEqual(port.busy_berths, 0)
        self.assertTrue(all(
            ship["rain_wait_time"] is None for ship in port.waiting_ships
        ))
        output = io.StringIO()
        with redirect_stdout(output):
            print_results(port)
        self.assertIn("Gelen gemi: 4", output.getvalue())
        self.assertIn("Ayrılan gemi: 2", output.getvalue())
        self.assertIn("Rıhtım bekleyen: 2", output.getvalue())
        self.assertIn("Hizmetteki gemi: 0", output.getvalue())

    def test_fractional_rain_end_dispatches_without_another_arrival(self):
        port = self.run_scenario(
            [(2, 1, "dry_cargo")], transitions=[1.5, 3.25], until=20
        )
        self.assertEqual(port.records[0]["server_assignment_time"], 3.25)
        self.assertEqual(port.records[0]["departure_time"], 13.25)
        self.assertEqual(port.records[0]["rain_wait_time"], 1.25)

    def test_rain_wait_counts_only_rainy_queue_intervals_including_full_berths(self):
        port = self.run_scenario(
            [(0, 1, "dry_cargo"), (0.5, 2, "container")],
            transitions=[1.5, 6, 8, 12, 14], initial_wet=True, until=30,
        )
        dry_cargo, container = port.records
        self.assertEqual(dry_cargo["server_assignment_time"], 10.5)
        self.assertEqual(dry_cargo["rain_wait_time"], 3.5)
        self.assertEqual(dry_cargo["departure_time"], 20.5)
        self.assertEqual(container["rain_wait_time"], 0)

    def test_horizon_excludes_completion_and_rain_end_at_exact_limit(self):
        port = self.run_scenario(
            [(0, 1, "container"), (1, 2, "dry_cargo")],
            transitions=[10], initial_wet=True, until=10,
        )
        self.assertIsNone(port.records[0]["departure_time"])
        self.assertIsNone(port.records[1]["server_assignment_time"])
        self.assertIsNone(port.records[1]["rain_wait_time"])
        self.assertEqual(port.busy_berths, 1)
        self.assertEqual(len(port.waiting_ships), 1)

    def test_generated_arrivals_enter_the_weather_aware_queue(self):
        env = simpy.Environment()
        port = Port(env, 1, WeatherCalendar([5], True, 30))
        with patch("arrivals.random.expovariate", side_effect=[1, 1, 100]), \
                patch("arrivals.random.random", side_effect=[0, 0.99]):
            env.process(generate_arrivals(env, port))
            self.run_until(env, port, 30)
        self.assertEqual(
            [(ship["ship_id"], ship["ship_type"], ship["arrival_time"],
              ship["server_assignment_time"], ship["departure_time"])
             for ship in port.records],
            [(1, "dry_cargo", 1, 12, 22), (2, "container", 2, 2, 12)],
        )

    def test_invalid_arrival_rate_fails_before_registering_a_ship(self):
        for invalid_rate in [None, 0, -1, float("inf"), float("nan")]:
            with self.subTest(arrival_rate=invalid_rate):
                env = simpy.Environment()
                port = Port(env, 1, WeatherCalendar([], False, 20))
                with patch("arrivals.ARRIVAL_RATE", invalid_rate):
                    env.process(generate_arrivals(env, port))
                    with self.assertRaisesRegex(ValueError, "positive finite"):
                        env.run(until=20)
                self.assertEqual(port.records, [])


if __name__ == "__main__":
    unittest.main()
