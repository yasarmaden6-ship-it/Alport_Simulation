# Geliş süresi ve gemi tipi için rastgele çekiliş yapmamızı sağlar.
import random

# Lambda değerinin sonsuz veya NaN olup olmadığını kontrol etmek için kullanılır.
from math import isfinite

# Geliş hızını ve kuru yük olasılığını config.py dosyasından alırız.
from config import ARRIVAL_RATE, DRY_CARGO_PROBABILITY


# Gemilerin geliş zamanlarını üretir; her gemi geldikten sonra tipini belirler.
# env: ortak saat, port: gemi kuyruğunu ve rıhtıma kabulü yöneten liman.
def generate_arrivals(env, port):
    # Lambda girilmiş, pozitif ve sonlu olmalı; birimi gemi/saat olmalıdır.
    if ARRIVAL_RATE is None or not isfinite(ARRIVAL_RATE) or ARRIVAL_RATE <= 0:
        # Geçerli lambda yoksa bir değer uydurmak yerine açıklayıcı hatayla dururuz.
        raise ValueError(
            "Set ARRIVAL_RATE in config.py to a positive finite number of ships per hour."
        )

    # Henüz gemi gelmedi; ilk gelen geminin numarası aşağıda 1 olacak.
    ship_id = 0

    # Ana dosyadaki env.run(...) süre sınırına ulaşana kadar yeni gelişler üretiriz.
    while True:
        # Bir sonraki gemiye kadar geçecek süreyi üstel dağılımdan çekeriz.
        # Fonksiyona doğrudan lambda verilir; çıkan süre saattir (0.25 saat = 15 dakika).
        waiting_time = random.expovariate(ARRIVAL_RATE)

        # Yalnızca geliş süreci bu kadar bekler; mevcut gemiler çalışmaya devam edebilir.
        yield env.timeout(waiting_time)

        # Bekleme bitti: yeni gemi geldi. Sıradaki gemi numarasını veririz.
        ship_id += 1

        # Gemi geldikten sonra, tipini belirlemek için ayrı bir sayı çekeriz.
        # Sayı 0 dahil, 1 hariç aralıktadır; 0.66'dan küçükse kuru yük olur.
        if random.random() < DRY_CARGO_PROBABILITY:
            ship_type = "dry_cargo"
        else:
            # Sayı 0.66 veya üzerindeyse konteyner gemisi olur.
            ship_type = "container"

        # Gemiyi ortak kuyruğa ekleriz; liman hava durumuna göre rıhtıma kabul eder.
        # Geminin ayrılmasını beklemeden sonraki geliş süresini çekeriz.
        port.arrive(ship_id, ship_type)
