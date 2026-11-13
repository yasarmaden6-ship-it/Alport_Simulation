import random

import simpy

from arrivals import generate_arrivals
from config import (
    INITIAL_WET, SEED, SERVER_COUNT, SIMULATION_HOURS,
    SIMULATION_START, WEATHER_SEED,
)
from port import Port
from results import print_results
from weather import generate_weather


if __name__ == "__main__":
    random.seed(SEED)
    weather = generate_weather(
        SIMULATION_START, SIMULATION_HOURS, INITIAL_WET, WEATHER_SEED
    )
    env = simpy.Environment()
    port = Port(env, SERVER_COUNT, weather, log_events=True)
    env.process(generate_arrivals(env, port))
    env.run(until=SIMULATION_HOURS)
    print_results(port)
