def print_event(port, event, record=None):
    hour = port.env.now
    wet, _ = port.weather.at(hour)
    dry_waiting = sum(
        ship["ship_type"] == "dry_cargo"
        for ship in port.waiting_ships
    )
    container_waiting = len(port.waiting_ships) - dry_waiting
    ship_label = "-"

    if record is not None:
        ship_type = "DRY" if record["ship_type"] == "dry_cargo" else "CONT"
        ship_label = f"{record['ship_id']}/{ship_type}"

    if event == "START":
        print("\nPORT EVENT TIMELINE", flush=True)
        header = (
            f"{'Day':>3} | {'Hour':>8} | {'Weather':<7} | "
            f"{'Event':<16} | {'Ship':<9} | {'Berths':>6} | "
            f"{'Queue':>6} | {'Dry':>4} | {'Cont':>4} | Details"
        )
        print(header, flush=True)
        print("-" * len(header), flush=True)
        detail = (
            "Only container admission is open"
            if wet else "FCFS admission is open for all ships"
        )
    elif event == "RAIN STARTED":
        detail = "Dry cargo admission closed; ongoing operations continue"
    elif event == "RAIN ENDED":
        detail = "FCFS admission reopened; ongoing operations continue"
    elif event == "QUEUED":
        reasons = []
        if wet and record["ship_type"] == "dry_cargo":
            reasons.append("rain: dry cargo admission closed")
        if port.busy_berths == port.capacity:
            reasons.append("all berths occupied")
        detail = "; ".join(reasons)
    elif event in ("ARRIVED/STARTED", "TAKEN FROM QUEUE"):
        wait = hour - record["arrival_time"]
        detail = f"Queue wait: {wait:.2f} h"
        if event == "TAKEN FROM QUEUE" and not port.waiting_ships:
            detail += "; queue cleared"
    elif event == "DEPARTED":
        duration = hour - record["server_assignment_time"]
        detail = f"Operation completed: {duration:.2f} h"
    else:
        raise ValueError(f"Unknown port event: {event}")

    weather_label = "RAIN" if wet else "DRY"
    occupancy = f"{port.busy_berths}/{port.capacity}"

    print(
        f"{int(hour // 24) + 1:>3} | {hour:>8.2f} | "
        f"{weather_label:<7} | {event:<16} | {ship_label:<9} | "
        f"{occupancy:>6} | {len(port.waiting_ships):>6} | "
        f"{dry_waiting:>4} | {container_waiting:>4} | {detail}",
        flush=True,
    )


def print_results(port):
    observation_end = (
        port.env.now
        if port.end_hour is None
        else min(port.env.now, port.end_hour)
    )
    departed_ships = [
        record for record in port.records
        if record["departure_time"] is not None
        and record["departure_time"] <= observation_end
    ]
    maximum_ships = (
        port.capacity * int(observation_end // port.operation_hours)
    )

    print("\nSIMULATION SUMMARY")
    print(
        f"Simulation duration: {observation_end / 24:.2f} days "
        f"({observation_end:g} hours)"
    )
    print("Only ships that completed their operation within this period are reported.")
    print(f"Required operation time per ship: {port.operation_hours:.2f} h")
    print(f"Number of berths: {port.capacity}")
    print(f"Theoretical maximum completed ships: {maximum_ships}")
    print(f"Completed ships: {len(departed_ships)}")

    if not departed_ships:
        print("No ships completed their operation within the simulation period.")
        return

    average_queue_time = sum(
        record["server_assignment_time"] - record["arrival_time"]
        for record in departed_ships
    ) / len(departed_ships)

    average_operation_time = sum(
        record["departure_time"] - record["server_assignment_time"]
        for record in departed_ships
    ) / len(departed_ships)

    average_port_stay = sum(
        record["departure_time"] - record["arrival_time"]
        for record in departed_ships
    ) / len(departed_ships)

    print(f"Average queue wait: {average_queue_time:.2f} h")
    print(f"Average operation time: {average_operation_time:.2f} h")
    print(f"Average port stay: {average_port_stay:.2f} h")

    print("\nCOMPLETED SHIPS")
    print("All times are measured in hours from the simulation start.")
    print("Rain wait is included in the total queue wait.")
    print("Operation = Departure - Start; Queue wait = Start - Arrival")
    print("DRY: dry cargo ship; CONT: container ship")

    header = (
        f"{'Ship':>4} | {'Type':<4} | {'Departure day':>13} | "
        f"{'Arrival':>8} | {'Start':>8} | {'Departure':>9} | "
        f"{'Operation':>9} | {'Queue wait':>10} | {'Rain wait':>9}"
    )
    print(header)
    print("-" * len(header))

    for record in departed_ships:
        ship_type = "DRY" if record["ship_type"] == "dry_cargo" else "CONT"
        wait = record["server_assignment_time"] - record["arrival_time"]
        operation = record["departure_time"] - record["server_assignment_time"]
        departure_day = int(record["departure_time"] // 24) + 1

        print(
            f"{record['ship_id']:>4} | {ship_type:<4} | "
            f"{departure_day:>13} | {record['arrival_time']:>8.2f} | "
            f"{record['server_assignment_time']:>8.2f} | "
            f"{record['departure_time']:>9.2f} | {operation:>9.2f} | "
            f"{wait:>10.2f} | {record['rain_wait_time']:>9.2f}"
        )