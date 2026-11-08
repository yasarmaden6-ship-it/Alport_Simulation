import random

import simpy

from ayarlar import RIHTIM_SAYISI, SEED, SIMULASYON_SURESI, YAGMUR_OLASILIGI
from gelisler import gemi_gelisleri
from sonuclar import sonuclari_yazdir


# Model yalnızca bu dosya doğrudan çalıştırıldığında başlar.
if __name__ == "__main__":
    random.seed(SEED)

    # Listedeki her değer bir saatin havasıdır; True yağmur, False kuru demektir.
    # Bütün gemiler aynı takvimi kullanır ve yalnızca mevcut saate bakar.
    yagmur_takvimi = [
        random.random() < YAGMUR_OLASILIGI
        for _ in range(SIMULASYON_SURESI)
    ]

    # Ortak simülasyon saati ve rıhtım kaynağı hazırlanır.
    env = simpy.Environment()
    rihtim = simpy.Resource(env, capacity=RIHTIM_SAYISI)
    kayitlar = []
    env.process(gemi_gelisleri(env, rihtim, yagmur_takvimi, kayitlar))

    # Tam bitiş saatindeki olaylar işlenmez; tamamlanmayan gemiler ayrıca sayılır.
    env.run(until=SIMULASYON_SURESI)
    sonuclari_yazdir(kayitlar, rihtim)
