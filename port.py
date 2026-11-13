from config import OPERATION_HOURS


# Queue for a server and advance the ship's work only during dry hours.
def ship_process(env, ship_id, ship_type, servers, rain_schedule, records):
    record = {
        "ship_id": ship_id,
        "ship_type": ship_type,
        "arrival_time": env.now,
        "server_assignment_time": None,
        "departure_time": None,
        "rain_delay": 0,
    }
    records.append(record)

    # SimPy queues requests in arrival order when all servers are occupied.
    with servers.request() as request:
        # Only this ship waits here until a server is assigned.
        yield request
        record["server_assignment_time"] = env.now
        remaining_work = OPERATION_HOURS

        while remaining_work > 0:
            # All ships read the same weather for the current hour.
            is_raining = rain_schedule[int(env.now)]
            yield env.timeout(1)

            # A rainy hour adds delay; a dry hour completes one hour of work.
            if is_raining:
                record["rain_delay"] += 1
            else:
                remaining_work -= 1

        record["departure_time"] = env.now
        # Leaving this block releases the server; rain pauses do not release it.
