from config import SIMULATION_HOURS


# Calculate and print queue times and port stays from the ship records.
def print_results(records, berths):
    # Queue times use berthed ships; total port stays use departed ships.
    berthed_ships = [record for record in records if record["berthing_time"] is not None]
    departed_ships = [record for record in records if record["departure_time"] is not None]

    print(f"Observation period: 0 <= hour < {SIMULATION_HOURS}")
    print(f"Ships arrived: {len(records)}")
    print(f"Ships departed: {len(departed_ships)}")
    print(f"Ships still queued: {len(berths.queue)}")
    print(f"Ships at berths: {berths.count}")

    if berthed_ships:
        average_queue_time = sum(
            record["berthing_time"] - record["arrival_time"] for record in berthed_ships
        ) / len(berthed_ships)
        print(f"Average queue time (berthed ships): {average_queue_time:.2f} hours")
    else:
        print("Average queue time: not available")

    if departed_ships:
        average_port_stay = sum(
            record["departure_time"] - record["arrival_time"] for record in departed_ships
        ) / len(departed_ships)
        print(f"Average port stay (departed ships): {average_port_stay:.2f} hours")

        print("\nTimes and rain delays for departed ships (hours):")
        print("Ship | Arrival | Berthing | Departure | Rain delay")
        for record in departed_ships:
            print(
                f"{record['ship_id']:>4} | {record['arrival_time']:>7} | "
                f"{record['berthing_time']:>8} | {record['departure_time']:>9} | "
                f"{record['rain_delay']:>10}"
            )
    else:
        print("Average port stay: not available")
