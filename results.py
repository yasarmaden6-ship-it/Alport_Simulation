# Print the state at a real event; queue columns exclude ships already in service.
def print_event(port, event, record=None):
    hour = port.env.now
    wet, _ = port.weather.at(hour)
    dry_waiting = sum(ship["ship_type"] == "dry_cargo" for ship in port.waiting_ships)
    container_waiting = len(port.waiting_ships) - dry_waiting
    ship_label = "-"
    if record is not None:
        ship_type = "KURU" if record["ship_type"] == "dry_cargo" else "KONT"
        ship_label = f"{record['ship_id']}/{ship_type}"

    if event == "BAŞLANGIÇ":
        print("\nLİMAN OLAY AKIŞI", flush=True)
        print("Gün 1: 0 <= saat < 24; Saat: başlangıçtan itibaren geçen süre", flush=True)
        print("Kuyruk/Kuru/Kont: bekleyen gemiler; Rıhtım: dolu/toplam", flush=True)
        header = (
            f"{'Gün':>3} | {'Saat':>8} | {'Hava':<7} | {'Olay':<14} | "
            f"{'Gemi':<9} | {'Rıhtım':>6} | {'Kuyruk':>6} | "
            f"{'Kuru':>4} | {'Kont':>4} | Açıklama"
        )
        print(header, flush=True)
        print("-" * len(header), flush=True)
        detail = "Yalnızca konteyner kabulü açık" if wet else "Tüm gemiler için FCFS açık"
    elif event == "YAĞMUR BAŞLADI":
        detail = "Yeni kuru yük kapalı; başlayan işler sürer"
    elif event == "YAĞMUR BİTTİ":
        detail = "FCFS yeniden açık; devam eden işler kesilmez"
    elif event == "KUYRUKTA":
        reasons = []
        if wet and record["ship_type"] == "dry_cargo":
            reasons.append("yağmur: kuru yük kabulü kapalı")
        if port.busy_berths == port.capacity:
            reasons.append("rıhtımlar dolu")
        detail = "; ".join(reasons)
    elif event in ("GELDİ/BAŞLADI", "SIRADAN ALINDI"):
        wait = hour - record["arrival_time"]
        detail = f"Bekleme: {wait:.2f} sa"
        if event == "SIRADAN ALINDI" and not port.waiting_ships:
            detail += "; kuyruk boşaldı"
    elif event == "AYRILDI":
        duration = hour - record["server_assignment_time"]
        detail = f"Hizmet tamamlandı: {duration:.2f} sa"
    else:
        raise ValueError(f"Unknown port event: {event}")

    weather_label = "YAĞMUR" if wet else "KURU"
    occupancy = f"{port.busy_berths}/{port.capacity}"
    print(
        f"{int(hour // 24) + 1:>3} | {hour:>8.2f} | {weather_label:<7} | "
        f"{event:<14} | {ship_label:<9} | {occupancy:>6} | "
        f"{len(port.waiting_ships):>6} | {dry_waiting:>4} | {container_waiting:>4} | {detail}",
        flush=True,
    )


# Summarize the observed run without treating the exclusive end as another day.
def print_results(port):
    assigned_ships = [record for record in port.records if record["server_assignment_time"] is not None]
    departed_ships = [record for record in port.records if record["departure_time"] is not None]

    print("\nSİMÜLASYON ÖZETİ")
    print(f"Gözlem süresi: {port.env.now / 24:.2f} gün (0 <= saat < {port.env.now:g})")
    print(f"Gelen gemi: {len(port.records)}")
    print(f"Ayrılan gemi: {len(departed_ships)}")
    print(f"Rıhtım bekleyen: {len(port.waiting_ships)}")
    print(f"Hizmetteki gemi: {port.busy_berths}")
    if port.peak_queue_time is None:
        print("En yüksek kuyruk: 0 gemi")
    else:
        print(
            f"En yüksek kuyruk: {port.peak_queue_size} gemi "
            f"(ilk kez Gün {int(port.peak_queue_time // 24) + 1}, saat {port.peak_queue_time:.2f})"
        )

    if assigned_ships:
        average_queue_time = sum(
            record["server_assignment_time"] - record["arrival_time"] for record in assigned_ships
        ) / len(assigned_ships)
        print(f"Ortalama rıhtım bekleme (kabul edilenler): {average_queue_time:.2f} sa")
    else:
        print("Ortalama rıhtım bekleme: henüz kabul edilen gemi yok")

    if departed_ships:
        average_port_stay = sum(
            record["departure_time"] - record["arrival_time"] for record in departed_ships
        ) / len(departed_ships)
        print(f"Ortalama limanda kalış (ayrılanlar): {average_port_stay:.2f} sa")

        print("\nAYRILAN GEMİLER (saatler başlangıçtan itibaren)")
        print("Yağmur bekleme, toplam kuyruk beklemesinin içindedir")
        header = (
            f"{'Gemi':>4} | {'Tür':<4} | {'Çıkış günü':>10} | {'Geliş':>8} | "
            f"{'Başlama':>8} | {'Çıkış':>8} | {'Bekleme':>8} | {'Yağmur':>8}"
        )
        print(header)
        print("-" * len(header))
        for record in departed_ships:
            ship_type = "KURU" if record["ship_type"] == "dry_cargo" else "KONT"
            wait = record["server_assignment_time"] - record["arrival_time"]
            print(
                f"{record['ship_id']:>4} | {ship_type:<4} | "
                f"{int(record['departure_time'] // 24) + 1:>10} | {record['arrival_time']:>8.2f} | "
                f"{record['server_assignment_time']:>8.2f} | {record['departure_time']:>8.2f} | "
                f"{wait:>8.2f} | {record['rain_wait_time']:>8.2f}"
            )
    else:
        print("Ortalama limanda kalış: henüz ayrılan gemi yok")
