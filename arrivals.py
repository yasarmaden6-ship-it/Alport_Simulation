import random
from math import isfinite

from config import ARRIVAL_RATE, DRY_CARGO_PROBABILITY


def generate_arrivals(env, port, until=None):
    """
    Generate ship arrivals and register them with the port.

    Parameters:
        env: The shared SimPy simulation environment.
        port: The Port object that manages the queue and berths.
        until: The arrival cutoff time, measured in simulation hours.
               Arrivals exactly at this time are excluded.
               If None, arrivals continue until the environment stops.
    """

    # The arrival rate must be a positive, finite value.
    # Its unit is ships per hour, not hours per ship.
    if (
        ARRIVAL_RATE is None
        or not isfinite(ARRIVAL_RATE)
        or ARRIVAL_RATE <= 0
    ):
        raise ValueError(
            "ARRIVAL_RATE must be a positive, finite number."
        )

    # Assign consecutive IDs to ships, starting with 1.
    ship_id = 0

    while True:
        # Generate the time until the next ship arrives.
        # Exponential interarrival times produce a Poisson arrival process.
        # The mean interarrival time is 1 / ARRIVAL_RATE hours.
        waiting_time = random.expovariate(ARRIVAL_RATE)

        # Stop generating ships if the next arrival would occur
        # at or after the cutoff time.
        if until is not None and env.now + waiting_time >= until:
            return

        # Advance this arrival process to the next arrival time.
        # Other ships and weather processes can continue meanwhile.
        yield env.timeout(waiting_time)

        ship_id += 1

        # Select the arriving ship's cargo type.
        # With probability 0.66, the ship carries dry cargo.
        # Otherwise, it is a container ship.
        if random.random() < DRY_CARGO_PROBABILITY:
            ship_type = "dry_cargo"
        else:
            ship_type = "container"

        # Register the ship with the port.
        # The port decides whether it can start immediately or must wait.
        # This call does not wait for the ship's operation to finish.
        port.arrive(ship_id, ship_type)