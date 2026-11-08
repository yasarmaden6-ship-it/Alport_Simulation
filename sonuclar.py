from ayarlar import SIMULASYON_SURESI


# Gemi kayıtlarından bekleme ve kalış sürelerini hesaplayıp ekrana yazdırır.
def sonuclari_yazdir(kayitlar, rihtim):
    # Kuyruk süresi yanaşanlar, toplam kalış süresi ayrılanlar için hesaplanır.
    yanasanlar = [kayit for kayit in kayitlar if kayit["yanasma_zamani"] is not None]
    ayrilanlar = [kayit for kayit in kayitlar if kayit["ayrilis_zamani"] is not None]

    print(f"Gözlem aralığı: 0 <= saat < {SIMULASYON_SURESI}")
    print(f"Gelen gemi: {len(kayitlar)}")
    print(f"Ayrılan gemi: {len(ayrilanlar)}")
    print(f"Kuyrukta kalan gemi: {len(rihtim.queue)}")
    print(f"Rıhtımda kalan gemi: {rihtim.count}")

    if yanasanlar:
        ortalama_kuyruk = sum(
            kayit["yanasma_zamani"] - kayit["gelis_zamani"] for kayit in yanasanlar
        ) / len(yanasanlar)
        print(f"Ortalama kuyruk süresi (yanaşanlar): {ortalama_kuyruk:.2f} saat")
    else:
        print("Ortalama kuyruk süresi: hesaplanamadı")

    if ayrilanlar:
        ortalama_kalis = sum(
            kayit["ayrilis_zamani"] - kayit["gelis_zamani"] for kayit in ayrilanlar
        ) / len(ayrilanlar)
        print(f"Ortalama limanda kalış (ayrılanlar): {ortalama_kalis:.2f} saat")

        print("\nAyrılan gemiler için zamanlar ve yağmur beklemesi (saat):")
        print("Gemi | Geliş | Yanaşma | Ayrılış | Yağmur beklemesi")
        for kayit in ayrilanlar:
            print(
                f"{kayit['gemi_no']:>4} | {kayit['gelis_zamani']:>5} | "
                f"{kayit['yanasma_zamani']:>7} | {kayit['ayrilis_zamani']:>7} | "
                f"{kayit['yagmur_beklemesi']:>16}"
            )
    else:
        print("Ortalama limanda kalış: hesaplanamadı")
