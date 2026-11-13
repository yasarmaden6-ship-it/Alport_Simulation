from config import SIMULATION_HOURS


# Calculate and print queue times and port stays from the ship records.
def print_results(records, servers):
    # Queue times use ships assigned a server; total port stays use departed ships.
    assigned_ships = [record for record in records if record["server_assignment_time"] is not None]
    departed_ships = [record for record in records if record["departure_time"] is not None]

    print(f"Observation period: 0 <= hour < {SIMULATION_HOURS}")
    print(f"Ships arrived: {len(records)}")
    print(f"Ships departed: {len(departed_ships)}")
    print(f"Ships still queued: {len(servers.queue)}")
    print(f"Ships at servers: {servers.count}")

    if assigned_ships:
        average_queue_time = sum(
            record["server_assignment_time"] - record["arrival_time"] for record in assigned_ships
        ) / len(assigned_ships)
        print(f"Average queue time (ships assigned a server): {average_queue_time:.2f} hours")
    else:
        print("Average queue time: not available")

    if departed_ships:
        average_port_stay = sum(
            record["departure_time"] - record["arrival_time"] for record in departed_ships
        ) / len(departed_ships)
        print(f"Average port stay (departed ships): {average_port_stay:.2f} hours")

        print("\nTimes and rain delays for departed ships (hours):")
        header = (
            f"{'Ship':>4} | {'Arrival':>9} | {'Server assigned':>15} | "
            f"{'Departure':>9} | {'Rain delay':>10}"
        )
        print(header)
        print("-" * len(header))
        for record in departed_ships:
            print(
                f"{record['ship_id']:>4} | {record['arrival_time']:>9.2f} | "
                f"{record['server_assignment_time']:>15.2f} | {record['departure_time']:>9.2f} | "
                f"{record['rain_delay']:>10.2f}"
            )
    else:
        print("Average port stay: not available")
