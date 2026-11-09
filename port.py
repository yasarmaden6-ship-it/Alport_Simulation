from config import OPERATION_HOURS


# Queue for a berth and advance the ship's work only during dry hours.
def ship_process(env, ship_id, berths, rain_schedule, records):
    record = {
        "ship_id": ship_id,
        "arrival_time": env.now,
        "berthing_time": None,
        "departure_time": None,
        "rain_delay": 0,
    }
    records.append(record)

    # SimPy queues requests in arrival order when all berths are occupied.
    with berths.request() as request:
        # Only this ship waits here until a berth is assigned.
        yield request
        record["berthing_time"] = env.now
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
        # Leaving this block releases the berth; rain pauses do not release it.
